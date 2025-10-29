def getCurrentActiveContainer(environment) {
    def blueContainer = environment == 'test' ? env.BE_TEST_BLUE_CONTAINER : env.BE_PROD_BLUE_CONTAINER
    def greenContainer = environment == 'test' ? env.BE_TEST_GREEN_CONTAINER : env.BE_PROD_GREEN_CONTAINER
    def bluePort = environment == 'test' ? env.BE_TEST_BLUE_PORT : env.BE_PROD_BLUE_PORT
    def greenPort = environment == 'test' ? env.BE_TEST_GREEN_PORT : env.BE_PROD_GREEN_PORT
    
    def blueRunning = sh(script: """docker ps --filter 'name=${blueContainer}' --format '{{.State}}'""", returnStdout: true).trim()
    def greenRunning = sh(script: """docker ps --filter 'name=${greenContainer}' --format '{{.State}}'""", returnStdout: true).trim()
    
    if (blueRunning == 'running') {
        echo "✅ Blue is running, deploying to Green"
        return ['blue', blueContainer, greenContainer, bluePort, greenPort]
    } else if (greenRunning == 'running') {
        echo "✅ Green is running, deploying to Blue"
        return ['green', greenContainer, blueContainer, greenPort, bluePort]
    } else {
        echo "ℹ️ No active container, deploying to Green"
        return ['none', blueContainer, greenContainer, bluePort, greenPort]
    }
}

def deployToInactiveEnvironment(environment, credentials, inactiveContainer, networkName, port) {
    withCredentials(credentials) {
        def tag = "${env.BE_IMAGE_NAME}:${environment}-${env.BUILD_NUMBER}"
        
        sh """
        # 비활성 환경에 새 컨테이너 배포
        docker stop ${inactiveContainer} || true
        docker rm ${inactiveContainer} || true
        
        docker run -d \\
            --name ${inactiveContainer} \\
            --restart unless-stopped \\
            --network ${networkName} \\
            --network ${env.DB_NETWORK} \\
            --network-alias backend-${environment}-new \\
            --publish ${port}:8080 \\
                   --env SPRING_PROFILES_ACTIVE=docker \\
            --env DB_USERNAME=\$DB_USERNAME \\
            --env DB_PASSWORD=\$DB_PASSWORD \\
            --env DB_NAME=\$DB_NAME \\
            --env REDIS_PASSWORD=\$REDIS_PASSWORD \\
            --env JWT_SECRET=\$JWT_SECRET \\
            --env JWT_ACCESS_TOKEN_EXPIRATION=\$JWT_ACCESS_EXPIRATION \\
            --env JWT_REFRESH_TOKEN_EXPIRATION=\$JWT_REFRESH_EXPIRATION \\
            ${tag}
        """
    }
}

def healthCheck(containerName, port) {
    def maxRetries = 30
    def retryCount = 0
    
    while (retryCount < maxRetries) {
        try {
            def response = sh(script: "curl -f http://localhost:${port}/api/actuator/health || exit 1", returnStatus: true)
            if (response == 0) {
                echo "✅ Health check passed for ${containerName}"
                return true
            }
        } catch (Exception e) {
            echo "⏳ Health check attempt ${retryCount + 1}/${maxRetries} failed for ${containerName}"
        }
        
        retryCount++
        sleep(2)
    }
    
    echo "❌ Health check failed for ${containerName} after ${maxRetries} attempts"
    return false
}

def switchTraffic(environment, activeContainer, inactiveContainer, networkName) {
    sh """
    # 기존 활성 컨테이너의 네트워크 별칭 제거
    docker network disconnect ${networkName} ${activeContainer} || true
    
    # 새 컨테이너를 활성화 (네트워크 별칭 변경)
    docker network connect --alias backend-${environment} ${networkName} ${inactiveContainer} || true
    
    # 기존 컨테이너 중지
    docker stop ${activeContainer} || true
    """
    
    echo "🔄 Traffic switched from ${activeContainer} to ${inactiveContainer}"
}

def cleanupOldResources() {
    echo "🧹 Cleaning up old Docker resources..."
    
    sh """
    # 중지된 컨테이너 제거 (Blue/Green 컨테이너 제외하고 오래된 것만)
    docker container prune -f --filter "until=24h" || true
    
    # 사용하지 않는 이미지 제거 (최근 5개 빌드 제외)
    docker images ${env.BE_IMAGE_NAME} --format "{{.ID}} {{.CreatedAt}}" | \\
        tail -n +6 | \\
        awk '{print \$1}' | \\
        xargs -r docker rmi -f || true
    
    # 사용하지 않는 볼륨 제거
    docker volume prune -f || true
    
    # 사용하지 않는 네트워크 제거 (db-network, app-network는 제외)
    docker network prune -f || true
    """
    
    echo "✅ Cleanup completed"
}

pipeline {
    agent any

    parameters {
        booleanParam(name: 'BUILD_BACKEND', defaultValue: false, description: '백엔드를 수동으로 빌드하고 배포하려면 체크하세요.')
        string(name: 'BRANCH_TO_BUILD', defaultValue: 'develop', description: '수동 빌드 시 기준 브랜치를 선택하세요 (develop 또는 main).')
        booleanParam(name: 'ROLLBACK_DEPLOYMENT', defaultValue: false, description: '이전 버전으로 롤백하려면 체크하세요.')
        booleanParam(name: 'CLEANUP_ONLY', defaultValue: false, description: '오래된 컨테이너/이미지만 정리하려면 체크하세요.')
    }

    /********************  환경 변수  ********************/
    environment {
        // --- Backend ---
        BE_IMAGE_NAME     = "rag-extension/backend-app"
        
        // Blue/Green 컨테이너 (Test)
        BE_TEST_BLUE_CONTAINER  = "rag-extension-be-test-blue"
        BE_TEST_GREEN_CONTAINER = "rag-extension-be-test-green"
        BE_TEST_BLUE_PORT       = "18080"
        BE_TEST_GREEN_PORT      = "18081"
        
        // Blue/Green 컨테이너 (Prod)
        BE_PROD_BLUE_CONTAINER  = "rag-extension-be-prod-blue"
        BE_PROD_GREEN_CONTAINER = "rag-extension-be-prod-green"
        BE_PROD_BLUE_PORT       = "8080"
        BE_PROD_GREEN_PORT      = "8081"

        // --- Docker 네트워크 ---
        APP_NETWORK_TEST = "app-network-test"
        APP_NETWORK_PROD = "app-network-prod"
        DB_NETWORK       = "db-network"
    }

    stages {

        /********************  변경 파일 확인  ********************/
        stage('Check for Changes') {
            when { 
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_BACKEND == true }
                }
            }
            steps {
                script {
                    echo "=== 환경 변수 확인 ==="
                    echo "GITLAB_OBJECT_KIND: ${env.GITLAB_OBJECT_KIND}"
                    echo "GIT_BRANCH: ${env.GIT_BRANCH}"
                    echo "REF: ${env.REF}"
                    echo "======================"
                    
                    if (env.GITLAB_OBJECT_KIND == 'push') {
                        echo "📝 Push 이벤트 감지 - 현재 브랜치로 배포"
                    } else if (params.BUILD_BACKEND == true) {
                        echo "📝 수동 빌드 실행"
                    }
                }
            }
        }

        /********************  Docker 네트워크 준비  ********************/
        stage('Prepare Docker Networks') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_BACKEND == true }
                }
            }
            steps {
                script {
                    // Docker 네트워크 생성
                    sh "docker network create ${APP_NETWORK_TEST} || true"
                    sh "docker network create ${APP_NETWORK_PROD} || true"
                    sh "docker network create ${DB_NETWORK} || true"
                    
                    echo "✅ Docker 네트워크 준비 완료"
                    echo "- Networks: ${APP_NETWORK_TEST}, ${APP_NETWORK_PROD}, ${DB_NETWORK}"
                }
            }
        }

        /********************  Docker 이미지 빌드  ********************/
        stage('Build Docker Image') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_BACKEND == true }
                }
            }
            steps {
                script {
                    def branch = ""
                    
                    if (env.GITLAB_OBJECT_KIND == 'push') {
                        branch = (env.REF ?: '').replaceAll('refs/heads/', '').trim()
                    } else if (params.BUILD_BACKEND == true) {
                        branch = (params.BRANCH_TO_BUILD ?: '').trim()
                    }

                    if (!branch) {
                        error "[Build Docker Image] 브랜치가 비어 있습니다."
                    }

                    echo "📝 빌드 대상 브랜치: ${branch}"
                    
                    def tag = "${BE_IMAGE_NAME}:${branch == 'main' ? 'prod' : 'test'}-${BUILD_NUMBER}"
                    
                    sh """
                    set -eux
                    docker build -t ${tag} .
                    """
                    
                    echo "✅ Docker 이미지 빌드 완료: ${tag}"
                }
            }
        }

        /******************** Blue/Green 배포  ********************/
        stage('Blue/Green Deploy') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_BACKEND == true }
                }
            }
            steps {
                script {
                    def branch = ""
                    
                    if (env.GITLAB_OBJECT_KIND == 'push') {
                        branch = (env.REF ?: '').replaceAll('refs/heads/', '').trim()
                    } else if (params.BUILD_BACKEND == true) {
                        branch = (params.BRANCH_TO_BUILD ?: '').trim()
                    }

                    if (!branch) {
                        error "[Blue/Green Deploy] 브랜치가 비어 있습니다."
                    }
                    
                    echo "📝 Blue/Green 배포 대상 브랜치: ${branch}"

                    def targetEnvironment = branch == 'main' ? 'prod' : 'test'
                    env.DEPLOY_TARGET_ENV = targetEnvironment
                    env.DEPLOY_NETWORK = branch == 'main' ? APP_NETWORK_PROD : APP_NETWORK_TEST

                    if (branch == 'develop') {
                        // Test 환경 Blue/Green 배포
                        def testCredentials = [
                            string(credentialsId: 'backend.db.username.test', variable: 'DB_USERNAME'),
                            string(credentialsId: 'backend.db.password.test', variable: 'DB_PASSWORD'),
                            string(credentialsId: 'backend.db.name.test', variable: 'DB_NAME'),
                            string(credentialsId: 'backend.redis.password', variable: 'REDIS_PASSWORD'),
                            string(credentialsId: 'backend.jwt.secret.test', variable: 'JWT_SECRET'),
                            string(credentialsId: 'backend.jwt.access.expiration', variable: 'JWT_ACCESS_EXPIRATION'),
                            string(credentialsId: 'backend.jwt.refresh.expiration', variable: 'JWT_REFRESH_EXPIRATION')
                        ]
                        
                        // 현재 활성 컨테이너 확인
                        def (currentEnv, activeContainer, inactiveContainer, activePort, inactivePort) = getCurrentActiveContainer('test')
                        echo "🔍 Current active environment: ${currentEnv}"
                        echo "📦 Active container: ${activeContainer} (port: ${activePort})"
                        echo "📦 Inactive container: ${inactiveContainer} (port: ${inactivePort})"
                        
                        // 비활성 환경에 새 버전 배포
                        deployToInactiveEnvironment('test', testCredentials, inactiveContainer, APP_NETWORK_TEST, inactivePort)

                        env.DEPLOY_ACTIVE_CONTAINER = activeContainer
                        env.DEPLOY_INACTIVE_CONTAINER = inactiveContainer
                        env.DEPLOY_ACTIVE_PORT = activePort
                        env.DEPLOY_INACTIVE_PORT = inactivePort
                        
                    } else if (branch == 'main') {
                        // Prod 환경 Blue/Green 배포
                        def prodCredentials = [
                            string(credentialsId: 'backend.db.username.prod', variable: 'DB_USERNAME'),
                            string(credentialsId: 'backend.db.password.prod', variable: 'DB_PASSWORD'),
                            string(credentialsId: 'backend.db.name.prod', variable: 'DB_NAME'),
                            string(credentialsId: 'backend.redis.password', variable: 'REDIS_PASSWORD'),
                            string(credentialsId: 'backend.jwt.secret.prod', variable: 'JWT_SECRET'),
                            string(credentialsId: 'backend.jwt.access.expiration', variable: 'JWT_ACCESS_EXPIRATION'),
                            string(credentialsId: 'backend.jwt.refresh.expiration', variable: 'JWT_REFRESH_EXPIRATION')
                        ]
                        
                        // 현재 활성 컨테이너 확인
                        def (currentEnv, activeContainer, inactiveContainer, activePort, inactivePort) = getCurrentActiveContainer('prod')
                        echo "🔍 Current active environment: ${currentEnv}"
                        echo "📦 Active container: ${activeContainer} (port: ${activePort})"
                        echo "📦 Inactive container: ${inactiveContainer} (port: ${inactivePort})"
                        
                        // 비활성 환경에 새 버전 배포
                        deployToInactiveEnvironment('prod', prodCredentials, inactiveContainer, APP_NETWORK_PROD, inactivePort)

                        env.DEPLOY_ACTIVE_CONTAINER = activeContainer
                        env.DEPLOY_INACTIVE_CONTAINER = inactiveContainer
                        env.DEPLOY_ACTIVE_PORT = activePort
                        env.DEPLOY_INACTIVE_PORT = inactivePort
                        
                    } else {
                        error "[Blue/Green Deploy] 지원하지 않는 브랜치='${branch}'. (develop/main 만 지원)"
                    }
                }
            }
        }

        /******************** Health Check  ********************/
        stage('Health Check') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_BACKEND == true }
                }
            }
            steps {
                script {
                    def branch = ""
                    
                    if (env.GITLAB_OBJECT_KIND == 'push') {
                        branch = (env.REF ?: '').replaceAll('refs/heads/', '').trim()
                    } else if (params.BUILD_BACKEND == true) {
                        branch = (params.BRANCH_TO_BUILD ?: '').trim()
                    }

                    def targetContainer = env.DEPLOY_INACTIVE_CONTAINER
                    def targetPort = env.DEPLOY_INACTIVE_PORT

                    if (!targetContainer?.trim() || !targetPort?.trim()) {
                        error "[Health Check] 배포 대상 정보를 찾을 수 없습니다."
                    }

                    echo "🏥 Health check for ${targetContainer} on port ${targetPort}"
                    
                    if (!healthCheck(targetContainer, targetPort)) {
                        error "❌ Health check failed for ${targetContainer}. Rolling back..."
                    }
                    
                    echo "✅ Health check passed for ${targetContainer}"
                }
            }
        }

        /******************** Traffic Switch  ********************/
        stage('Switch Traffic') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_BACKEND == true }
                }
            }
            steps {
                script {
                    def branch = ""
                    
                    if (env.GITLAB_OBJECT_KIND == 'push') {
                        branch = (env.REF ?: '').replaceAll('refs/heads/', '').trim()
                    } else if (params.BUILD_BACKEND == true) {
                        branch = (params.BRANCH_TO_BUILD ?: '').trim()
                    }

                    def targetEnvironment = env.DEPLOY_TARGET_ENV
                    def networkName = env.DEPLOY_NETWORK
                    def activeContainer = env.DEPLOY_ACTIVE_CONTAINER
                    def inactiveContainer = env.DEPLOY_INACTIVE_CONTAINER

                    if (!inactiveContainer?.trim()) {
                        error "[Switch Traffic] 전환할 대상 컨테이너 정보를 찾을 수 없습니다."
                    }

                    echo "🔄 Switching traffic from ${activeContainer ?: 'none'} to ${inactiveContainer}"
                    
                    // 트래픽 전환
                    switchTraffic(targetEnvironment, activeContainer, inactiveContainer, networkName)
                    
                    echo "🎉 Blue/Green deployment completed successfully!"
                    echo "📊 New active container: ${inactiveContainer}"
                }
            }
        }

        /******************** Rollback  ********************/
        stage('Rollback') {
            when {
                expression { params.ROLLBACK_DEPLOYMENT == true }
            }
            steps {
                script {
                    def branch = (params.BRANCH_TO_BUILD ?: '').trim()
                    if (!branch) {
                        error "[Rollback] 롤백할 브랜치를 선택하세요."
                    }

                    def environment = branch == 'main' ? 'prod' : 'test'
                    def networkName = branch == 'main' ? APP_NETWORK_PROD : APP_NETWORK_TEST
                    
                    // 현재 활성/비활성 컨테이너 확인
                    def (currentEnv, activeContainer, inactiveContainer, activePort, inactivePort) = getCurrentActiveContainer(environment)
                    
                    echo "🔄 Rolling back from ${activeContainer} (${activePort}) to ${inactiveContainer} (${inactivePort})"
                    
                    // 트래픽을 이전 버전으로 전환
                    switchTraffic(environment, activeContainer, inactiveContainer, networkName)
                    
                    echo "✅ Rollback completed successfully!"
                    echo "📊 Active container after rollback: ${inactiveContainer}"
                }
            }
        }

        /******************** Cleanup  ********************/
        stage('Cleanup Old Resources') {
            when {
                expression { params.CLEANUP_ONLY == true }
            }
            steps {
                script {
                    echo "🧹 Manual cleanup requested"
                    cleanupOldResources()
                }
            }
        }
    }
    
    post {
        success {
            script {
                echo "✅ Pipeline succeeded!"
                
                // 성공 시에만 오래된 리소스 정리
                if (env.GITLAB_OBJECT_KIND == 'push' || params.BUILD_BACKEND == true) {
                    cleanupOldResources()
                }
            }
        }
        
        failure {
            script {
                echo "❌ Pipeline failed!"
                
                // 실패 시 롤백 정보 출력
                if (env.GITLAB_OBJECT_KIND == 'push' || params.BUILD_BACKEND == true) {
                    echo "🔄 Consider running manual rollback with ROLLBACK_DEPLOYMENT parameter"
                }
            }
        }
        
        always {
            echo "📦 Pipeline finished with status: ${currentBuild.currentResult}"
        }
    }
}


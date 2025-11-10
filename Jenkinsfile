def getCurrentActiveContainer(environment) {
    def blueContainer = environment == 'test' ? env.BE_TEST_BLUE_CONTAINER : env.BE_PROD_BLUE_CONTAINER
    def greenContainer = environment == 'test' ? env.BE_TEST_GREEN_CONTAINER : env.BE_PROD_GREEN_CONTAINER
    def bluePort = environment == 'test' ? env.BE_TEST_BLUE_PORT : env.BE_PROD_BLUE_PORT
    def greenPort = environment == 'test' ? env.BE_TEST_GREEN_PORT : env.BE_PROD_GREEN_PORT
    
    def blueState = sh(script: """docker inspect --format='{{.State.Status}}' ${blueContainer} 2>/dev/null || echo 'none'""", returnStdout: true).trim()
    def greenState = sh(script: """docker inspect --format='{{.State.Status}}' ${greenContainer} 2>/dev/null || echo 'none'""", returnStdout: true).trim()
    
    echo "🔍 Blue container state: ${blueState}, Green container state: ${greenState}"

    if (blueState == 'running' && greenState != 'running') {
        echo "✅ Blue is running, deploying to Green"
        return ['blue', blueContainer, greenContainer, bluePort, greenPort]
    } else if (greenState == 'running' && blueState != 'running') {
        echo "✅ Green is running, deploying to Blue"
        return ['green', greenContainer, blueContainer, greenPort, bluePort]
    } else if (blueState == 'running' && greenState == 'running') {
        def blueUpdated = sh(script: """docker inspect --format='{{.State.StartedAt}}' ${blueContainer}""", returnStdout: true).trim()
        def greenUpdated = sh(script: """docker inspect --format='{{.State.StartedAt}}' ${greenContainer}""", returnStdout: true).trim()

        echo "⚖️ Both containers running. Blue started at ${blueUpdated}, Green started at ${greenUpdated}"

        if (blueUpdated.compareTo(greenUpdated) > 0) {
            echo "➡️ Blue is newer, treating Blue as active"
            return ['blue', blueContainer, greenContainer, bluePort, greenPort]
        } else {
            echo "➡️ Green is newer, treating Green as active"
            return ['green', greenContainer, blueContainer, greenPort, bluePort]
        }
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
            -v /var/run/docker.sock:/var/run/docker.sock \\
            --env SPRING_PROFILES_ACTIVE=docker \\
            --env DB_USERNAME=\$DB_USERNAME \\
            --env DB_PASSWORD=\$DB_PASSWORD \\
            --env DB_NAME=\$DB_NAME \\
            --env REDIS_PASSWORD=\$REDIS_PASSWORD \\
            --env MONGODB_DATABASE=\$MONGODB_DATABASE \\
            --env MONGODB_USERNAME=\$MONGODB_USERNAME \\
            --env MONGODB_PASSWORD=\$MONGODB_PASSWORD \\
            --env JWT_SECRET=\$JWT_SECRET \\
            --env JWT_ACCESS_TOKEN_EXPIRATION=\$JWT_ACCESS_EXPIRATION \\
            --env JWT_REFRESH_TOKEN_EXPIRATION=\$JWT_REFRESH_EXPIRATION \\
            --env RUNPOD_API_KEY=\$RUNPOD_API_KEY \\
            ${tag}
        """
    }
}

def healthCheck(containerName, port, networkName) {
    def maxRetries = 30
    def retryCount = 0
    
    while (retryCount < maxRetries) {
        try {
            def response = sh(
                script: """
                docker run --rm --network ${networkName} curlimages/curl:8.8.0 \
                    -f http://${containerName}:8080/api/v1/actuator/health >/dev/null
                """,
                returnStatus: true
            )

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
    // Nginx upstream 설정 파일명
    def upstreamFile = environment == 'test' ? 
        'spring-dev-active-upstream.conf' : 
        'spring-active-upstream.conf'
    
    def upstreamName = environment == 'test' ? 'spring_dev_active' : 'spring_active'
    
    sh """
    set -e
    
    # 임시 컨테이너로 호스트 파일시스템에 접근하여 upstream 설정 업데이트
    docker run --rm -v /home/ubuntu/nginx/conf/upstreams:/upstreams alpine sh -c \
        "echo 'upstream ${upstreamName} { server ${inactiveContainer}:8080; }' > /upstreams/${upstreamFile}"
    
    # Nginx 설정 리로드
    docker exec nginx nginx -s reload
    
    echo "✅ Nginx upstream updated to ${inactiveContainer}"
    
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
                            string(credentialsId: 'backend.mongodb.database', variable: 'MONGODB_DATABASE'),
                            string(credentialsId: 'backend.mongodb.username', variable: 'MONGODB_USERNAME'),
                            string(credentialsId: 'backend.mongodb.password', variable: 'MONGODB_PASSWORD'),
                            string(credentialsId: 'backend.jwt.secret.test', variable: 'JWT_SECRET'),
                            string(credentialsId: 'backend.jwt.access.expiration', variable: 'JWT_ACCESS_EXPIRATION'),
                            string(credentialsId: 'backend.jwt.refresh.expiration', variable: 'JWT_REFRESH_EXPIRATION'),
                            string(credentialsId: 'RUNPOD_API_KEY', variable: 'RUNPOD_API_KEY')
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
                            string(credentialsId: 'backend.mongodb.database', variable: 'MONGODB_DATABASE'),
                            string(credentialsId: 'backend.mongodb.username', variable: 'MONGODB_USERNAME'),
                            string(credentialsId: 'backend.mongodb.password', variable: 'MONGODB_PASSWORD'),
                            string(credentialsId: 'backend.jwt.secret.prod', variable: 'JWT_SECRET'),
                            string(credentialsId: 'backend.jwt.access.expiration', variable: 'JWT_ACCESS_EXPIRATION'),
                            string(credentialsId: 'backend.jwt.refresh.expiration', variable: 'JWT_REFRESH_EXPIRATION'),
                            string(credentialsId: 'RUNPOD_API_KEY', variable: 'RUNPOD_API_KEY')
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
                    def networkName = env.DEPLOY_NETWORK
                    
                    if (!targetContainer?.trim() || !targetPort?.trim()) {
                        error "[Health Check] 배포 대상 정보를 찾을 수 없습니다."
                    }
                    
                    echo "🏥 Health check for ${targetContainer} on port ${targetPort}"
                    
                    if (!healthCheck(targetContainer, targetPort, networkName)) {
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
        always {
            script {
                // 공통 정보 수집 (한 번만 실행)
                def branch    = resolveBranch()
                def mention   = resolvePusherMention()
                def commitMsg = sh(script: "git log -1 --pretty=%s", returnStdout: true).trim()
                def commitUrl = env.GIT_COMMIT_URL ?: ""
                
                def buildInfo = [
                    branch   : branch,
                    mention  : mention,
                    buildUrl : env.BUILD_URL,
                    commit   : [msg: commitMsg, url: commitUrl]
                ]
                
                // 빌드 결과에 따라 알림 전송
                if (currentBuild.result == 'SUCCESS' || currentBuild.result == null) {
                    echo "🎉 POST: 빌드 성공 – Mattermost 알림 전송"
                
                // 성공 시에만 오래된 리소스 정리
                if (env.GITLAB_OBJECT_KIND == 'push' || params.BUILD_BACKEND == true) {
                    cleanupOldResources()
                }
                    
                    sendMMNotify(true, buildInfo)
                    
                } else if (currentBuild.result == 'FAILURE') {
                    echo "🚨 POST: 빌드 실패 – 로그 추출 후 Mattermost 알림 전송"
                    
                    // Jenkins 내장 API로 로그 추출 (마지막 150줄)
                    def logLines = []
                    try {
                        def rawBuild = currentBuild.rawBuild
                        def logText = rawBuild.getLog(150).join('\n')
                        
                        // 민감정보 마스킹
                        logText = logText
                            .replaceAll(/(?i)(token|secret|password|passwd|apikey|api_key)\s*[:=]\s*\S+/, '$1=[REDACTED]')
                            .replaceAll(/AKIA[0-9A-Z]{16}/, 'AKIA[REDACTED]')
                        
                        buildInfo.details = "```text\n${logText}\n```"
                    } catch (Exception e) {
                        echo "⚠️ 로그 추출 실패: ${e.message}"
                        buildInfo.details = "```text\n로그를 가져올 수 없습니다.\n```"
                    }
                    
                    sendMMNotify(false, buildInfo)
                
                // 실패 시 롤백 정보 출력
                if (env.GITLAB_OBJECT_KIND == 'push' || params.BUILD_BACKEND == true) {
                    echo "🔄 Consider running manual rollback with ROLLBACK_DEPLOYMENT parameter"
            }
        }
        
            echo "📦 Pipeline finished with status: ${currentBuild.currentResult}"
        }
        }
    }
}

// 브랜치 해석: BRANCH_NAME → GIT_REF → git
def resolveBranch() {
    if (env.BRANCH_NAME) return env.BRANCH_NAME
    if (env.REF) return env.REF.replaceFirst(/^refs\/heads\//, '')
    return sh(script: "git name-rev --name-only HEAD || git rev-parse --abbrev-ref HEAD", returnStdout: true).trim()
}

// @username (웹훅의 user_username) 우선, 없으면 커밋 작성자 표시
def resolvePusherMention() {
    def u = env.GIT_PUSHER_USERNAME?.trim()
    if (u) return "@${u}"
    return sh(script: "git --no-pager show -s --format='%an <%ae>' HEAD", returnStdout: true).trim()
}

// 매터모스트 알림 전송
def sendMMNotify(boolean success, Map info) {
    def titleLine = success ? "## :jenkins7: 백엔드 빌드 성공 ✅"
                            : "## :angry_jenkins: 백엔드 빌드 실패 ❌"
    def lines = []
    if (info.mention) lines << "**작성자**: ${info.mention}"
    if (info.branch)  lines << "**대상 브랜치**: `${info.branch}`"
    if (info.commit?.msg) {
        def commitLine = info.commit?.url ? "[${info.commit.msg}](${info.commit.url})" : info.commit.msg
        lines << "**커밋**: ${commitLine}"
    }
    if (info.buildUrl) {
        lines << "**빌드 상세**: [Details](${info.buildUrl})"
    }
    if (!success && info.details) {
        lines << "**에러 로그**:\n${info.details}"
    }
    
    def text = "${titleLine}\n" + (lines ? ("\n" + lines.join("\n")) : "")
    
    // 안전 전송(크리덴셜 경고 없음)
    writeFile file: 'payload.json', text: groovy.json.JsonOutput.toJson([
        text      : text,
        username  : "Jenkins",
        icon_emoji: ":jenkins7:"
    ])
    
    withCredentials([string(credentialsId: 'mattermost-webhook', variable: 'MM_WEBHOOK')]) {
        sh(script: '''
            curl -sS -f -X POST -H 'Content-Type: application/json' \
                --data-binary @payload.json \
                "$MM_WEBHOOK" || true
        ''')
    }
}


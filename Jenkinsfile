pipeline {
    agent any

    parameters {
        booleanParam(name: 'BUILD_FRONTEND', defaultValue: false, description: '프론트엔드를 수동으로 빌드하고 배포하려면 체크하세요.')
        string(name: 'BRANCH_TO_BUILD', defaultValue: 'develop', description: '수동 빌드 시 기준 브랜치를 선택하세요 (develop 또는 main).')
    }

    /********************  환경 변수  ********************/
    environment {
        // --- Frontend ---
        FE_IMAGE_NAME     = "rag-extension/frontend-app"
        FE_TEST_CONTAINER = "rag-extension-fe-test"
        FE_PROD_CONTAINER = "rag-extension-fe-prod"

        // --- Docker Swarm 네트워크 ---
        APP_NETWORK_TEST = "app-network-test"
        APP_NETWORK_PROD = "app-network-prod"
    }

    stages {

        /********************  변경 파일 확인  ********************/
        stage('Check for Changes') {
            when { expression { (env.MR_STATE ?: '') == 'merged' } }
            steps {
                script {
                    env.DO_FRONTEND_BUILD = 'false'

                    sh "git fetch --all >/dev/null 2>&1 || true"
                    def changed = sh(script: "git diff --name-only origin/${env.TARGET_BRANCH}...origin/${env.SOURCE_BRANCH}",returnStdout: true).trim()

                    echo "=== 변경된 파일 목록 ==="
                    echo changed
                    echo "========================"

                    if (changed.contains('frontend-repo/')) env.DO_FRONTEND_BUILD = 'true'

                    echo "=== 빌드 결정 사항 ==="
                    echo "DO_FRONTEND_BUILD: ${env.DO_FRONTEND_BUILD}"
                    echo "====================="
                }
            }
        }

        /********************  Docker Swarm 초기화 및 네트워크 준비  ********************/
        stage('Initialize Docker Swarm and Networks') {
            when {
                anyOf {
                    expression { (env.MR_STATE ?: '') == 'merged' }
                    expression { params.BUILD_FRONTEND == true }
                }
            }
            steps {
                script {
                    // Docker Swarm 초기화
                    sh "docker swarm init || true"
                    
                    // Overlay 네트워크 생성
                    // Test 환경 네트워크
                    sh "docker network create --driver overlay --attachable ${APP_NETWORK_TEST} || true"
                    
                    // Production 환경 네트워크
                    sh "docker network create --driver overlay --attachable ${APP_NETWORK_PROD} || true"
                    
                    echo "✅ Docker Swarm 네트워크 준비 완료"
                    echo "- Application Networks: ${APP_NETWORK_TEST}, ${APP_NETWORK_PROD}"
                }
            }
        }

        /******************** 프론트엔드 배포  ********************/
        stage('Deploy Frontend') {
            when {
                anyOf {
                    expression { (env.MR_STATE ?: '') == 'merged' && env.DO_FRONTEND_BUILD == 'true' }
                    expression { params.BUILD_FRONTEND == true }
                }
            }
            steps {
                script {
                    def branch = (env.MR_STATE == 'merged') ? (env.TARGET_BRANCH ?: '').trim() : (params.BRANCH_TO_BUILD ?: '').trim()

                    if (!branch) {
                        error "[Deploy Frontend] 브랜치가 비어 있습니다. TARGET_BRANCH 또는 BRANCH_TO_BUILD를 확인하세요."
                    }

                    if (branch == 'develop') {
                        withCredentials([file(credentialsId: '.env.development', variable: 'ENV_FILE')]) {
                            def tag = "${FE_IMAGE_NAME}:test-${BUILD_NUMBER}"

                            sh """
                            set -eux
                            rm -rf _docker_ctx
                            mkdir -p _docker_ctx
                            tar --no-same-owner -cf - --exclude=.git --exclude=_docker_ctx --exclude=.env . | (cd _docker_ctx && tar -xf -)
                            chmod -R 755 _docker_ctx
                            cp "\$ENV_FILE" _docker_ctx/.env
                            ls -la _docker_ctx/.env
                            cat _docker_ctx/.env
                            docker build -t ${tag} --build-arg ENV=test _docker_ctx
                            """
                            
                            // Test: 포트 7443
                            sh """
                            if docker service inspect ${FE_TEST_CONTAINER} >/dev/null 2>&1; then
                                docker service update \\
                                    --image ${tag} \\
                                    ${FE_TEST_CONTAINER}
                            else
                                docker service create \\
                                    --name ${FE_TEST_CONTAINER} \\
                                    --network ${APP_NETWORK_TEST} \\
                                    --publish 7443:80 \\
                                    --replicas 1 \\
                                    --constraint 'node.hostname==worker' \\
                                    --update-failure-action rollback \\
                                    ${tag}
                            fi
                            """
                        }
                    } else if (branch == 'main') {
                        withCredentials([file(credentialsId: '.env.production', variable: 'ENV_FILE')]) {
                            def tag = "${FE_IMAGE_NAME}:prod-${BUILD_NUMBER}"

                            sh """
                            set -eux
                            rm -rf _docker_ctx
                            mkdir -p _docker_ctx
                            tar --no-same-owner -cf - --exclude=.git --exclude=_docker_ctx --exclude=.env* . | (cd _docker_ctx && tar -xf -)
                            chmod -R 755 _docker_ctx
                            cp "\$ENV_FILE" _docker_ctx/.env.production
                            ls -la _docker_ctx/.env.production
                            cat _docker_ctx/.env.production
                            docker build -t ${tag} --build-arg ENV=prod _docker_ctx
                            """
                            
                            // Prod: 포트 80, 443
                            sh """
                            if docker service inspect ${FE_PROD_CONTAINER} >/dev/null 2>&1; then
                                docker service update \\
                                    --image ${tag} \\
                                    ${FE_PROD_CONTAINER}
                            else
                                docker service create \\
                                    --name ${FE_PROD_CONTAINER} \\
                                    --network ${APP_NETWORK_PROD} \\
                                    --publish 80:80 \\
                                    --publish 443:443 \\
                                    --replicas 1 \\
                                    --constraint 'node.hostname==worker' \\
                                    --update-failure-action rollback \\
                                    ${tag}
                            fi
                            """
                        }
                    } else {
                        error "[Deploy Frontend] 지원하지 않는 브랜치='${branch}'. (develop/main 만 지원)"
                    }
                }
            }
        }
    }
    
    post {
        always {
            echo "📦 Pipeline finished with status: ${currentBuild.currentResult}"
        }
    }
}


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

        // --- Docker 네트워크 ---
        APP_NETWORK_TEST = "app-network-test"
        APP_NETWORK_PROD = "app-network-prod"
    }

    stages {

        /********************  변경 파일 확인  ********************/
        stage('Check for Changes') {
            when { 
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_FRONTEND == true }
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
                    } else if (params.BUILD_FRONTEND == true) {
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
                    expression { params.BUILD_FRONTEND == true }
                }
            }
            steps {
                script {
                    // Docker 네트워크 생성
                    sh "docker network create ${APP_NETWORK_TEST} || true"
                    sh "docker network create ${APP_NETWORK_PROD} || true"
                    
                    echo "✅ Docker 네트워크 준비 완료"
                    echo "- Networks: ${APP_NETWORK_TEST}, ${APP_NETWORK_PROD}"
                }
            }
        }

        /******************** 프론트엔드 배포  ********************/
        stage('Deploy Frontend') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_FRONTEND == true }
                }
            }
            steps {
                script {
                    def branch = ""
                    
                    if (env.GITLAB_OBJECT_KIND == 'push') {
                        // Push 이벤트: REF에서 브랜치 추출
                        branch = (env.REF ?: '').replaceAll('refs/heads/', '').trim()
                    } else if (params.BUILD_FRONTEND == true) {
                        // 수동 빌드: 파라미터 브랜치 사용
                        branch = (params.BRANCH_TO_BUILD ?: '').trim()
                    }

                    if (!branch) {
                        error "[Deploy Frontend] 브랜치가 비어 있습니다. Push/수동 빌드 조건을 확인하세요."
                    }
                    
                    echo "📝 배포 대상 브랜치: ${branch}"

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
                            
                            sh """
                            # 기존 컨테이너 중지 및 삭제
                            docker stop ${FE_TEST_CONTAINER} || true
                            docker rm ${FE_TEST_CONTAINER} || true
                            
                            # 새 컨테이너 실행
                            docker run -d \\
                                --name ${FE_TEST_CONTAINER} \\
                                --restart unless-stopped \\
                                --network ${APP_NETWORK_TEST} \\
                                --publish 17443:80 \\
                                ${tag}
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
                            
                            sh """
                            # 기존 컨테이너 중지 및 삭제
                            docker stop ${FE_PROD_CONTAINER} || true
                            docker rm ${FE_PROD_CONTAINER} || true
                            
                            # 새 컨테이너 실행
                            docker run -d \\
                                --name ${FE_PROD_CONTAINER} \\
                                --restart unless-stopped \\
                                --network ${APP_NETWORK_PROD} \\
                                --publish 7443:80 \\
                                ${tag}
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


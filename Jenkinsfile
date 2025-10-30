pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

    parameters {
        booleanParam(name: 'BUILD_PYTHON_BACKEND', defaultValue: true, description: 'Python Backend를 수동으로 빌드하고 배포하려면 체크하세요.')
        string(name: 'BRANCH_TO_BUILD', defaultValue: 'develop', description: '수동 빌드 시 기준 브랜치를 선택하세요 (develop 또는 main).')
        booleanParam(name: 'CLEANUP_ONLY', defaultValue: false, description: '오래된 컨테이너/이미지 정리만 수행')
    }

    environment {
        // Image & Container
        PYTHON_BACKEND_IMAGE_NAME = "hebees/python-backend"
        PYTHON_BACKEND_CONTAINER  = "hebees-python-backend"

        // Networks
        APP_NETWORK_TEST = "app-network-test"
        APP_NETWORK_PROD = "app-network-prod"
        DB_NETWORK = "db-network"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'ls -al'
            }
        }

        stage('Prepare Docker Networks') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_PYTHON_BACKEND == true }
                }
            }
            steps {
                sh "docker network create ${APP_NETWORK_TEST} || true"
                sh "docker network create ${APP_NETWORK_PROD} || true"
                sh "docker network create ${DB_NETWORK} || true"
            }
        }

        stage('Build Docker Image') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_PYTHON_BACKEND == true }
                }
            }
            steps {
                script {
                    // 브랜치 결정: 웹훅(ref) 우선, 없으면 파라미터
                    def branch = ''
                    if (env.GITLAB_OBJECT_KIND == 'push') {
                        branch = (env.REF ?: '').replaceAll('refs/heads/', '').trim()
                    }
                    if (!branch) {
                        branch = (params.BRANCH_TO_BUILD ?: '').trim()
                    }
                    if (!branch) { error '[Build Docker Image] 브랜치가 비어 있습니다.' }
                    echo "빌드 대상 브랜치: ${branch}"

                    def tag = "${PYTHON_BACKEND_IMAGE_NAME}:${env.BUILD_NUMBER}"
                    sh """
                    set -eux
                    docker build -t ${tag} .
                    """
                    env.PYTHON_BACKEND_BUILD_TAG = tag
                }
            }
        }

        stage('Deploy Docker Container') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_PYTHON_BACKEND == true }
                }
            }
            steps {
                withCredentials([file(credentialsId: 'python-backend-repo.env', variable: 'PYTHON_BACKEND_ENV_FILE')]) {
                    sh '''
                    set -eux
                    # 기존 컨테이너 종료/삭제
                    docker stop "$PYTHON_BACKEND_CONTAINER" || true
                    docker rm "$PYTHON_BACKEND_CONTAINER" || true

                    # 컨테이너 실행: --env-file로 환경 변수 주입
                    docker run -d \
                        --name "$PYTHON_BACKEND_CONTAINER" \
                        --restart unless-stopped \
                        --network "$APP_NETWORK_TEST" \
                        --env-file "$PYTHON_BACKEND_ENV_FILE" \
                        "$PYTHON_BACKEND_BUILD_TAG"

                    # 추가 네트워크 연결 (prod, db)
                    docker network connect "$APP_NETWORK_PROD" "$PYTHON_BACKEND_CONTAINER" || true
                    docker network connect "$DB_NETWORK" "$PYTHON_BACKEND_CONTAINER" || true
                    '''
                }
            }
        }

        stage('Health Check') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_PYTHON_BACKEND == true }
                }
            }
            steps {
                script {
                    def maxRetries = 30
                    def ok = false
                    for (int i = 0; i < maxRetries; i++) {
                        def status = sh(script: '''
                            docker run --rm --network "$APP_NETWORK_TEST" curlimages/curl:8.8.0 \
                                -fsS http://$PYTHON_BACKEND_CONTAINER:8000/health >/dev/null
                        ''', returnStatus: true)
                        if (status == 0) { ok = true; break }
                        sleep 2
                    }
                    if (!ok) { error "Health check failed for ${PYTHON_BACKEND_CONTAINER}" }
                }
            }
        }

        stage('Cleanup Old Images (Optional)') {
            when { expression { params.CLEANUP_ONLY == true } }
            steps {
                sh "docker image prune -f || true"
            }
        }
    }

    post {
        always { echo "Pipeline finished: ${currentBuild.currentResult}" }
    }
}

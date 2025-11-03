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
        /********************  서브모듈 체크아웃  ********************/
        stage('Checkout Submodules') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_FRONTEND == true }
                }
            }
            steps {
                sh '''
                set -eux
                git submodule sync --recursive
                git submodule update --init --recursive
                git submodule status
                ls -la frontend-repo || true
                '''
            }
        }

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

        /********************  pnpm-lock.yaml 업데이트  ********************/
        stage('Update pnpm-lock.yaml') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_FRONTEND == true }
                }
            }
            steps {
                sh '''
                set -eux
                # package.json 존재 시에만 lockfile 업데이트 시도
                if [ -f package.json ]; then
                  docker run --rm -v "$PWD":/app -w /app node:22.10.0-alpine sh -c "
                      npm install -g pnpm && \
                      pnpm install && \
                      chown -R $(id -u):$(id -g) pnpm-lock.yaml 2>/dev/null || true
                  "
                else
                  echo "skip pnpm install: package.json not found in workspace"
                fi
                # 업데이트 확인 (존재만 확인)
                if [ -f pnpm-lock.yaml ]; then
                    echo "✅ pnpm-lock.yaml present"
                    ls -lh pnpm-lock.yaml
                else
                    echo "❌ pnpm-lock.yaml missing"
                    exit 1
                fi
                '''
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

                            sh '''
                            set -eux
                            # Docker 빌드 컨텍스트 준비
                            rm -rf _docker_ctx
                            mkdir -p _docker_ctx
                            SRC_DIR="."
                            if [ -d frontend-repo ]; then SRC_DIR="frontend-repo"; fi
                            TMP_ARCHIVE="$(mktemp -t ctx.XXXXXX.tar)"
                            tar -C "$SRC_DIR" --no-same-owner -cf "$TMP_ARCHIVE" --exclude=.git --exclude=_docker_ctx --exclude=.env .
                            tar -C _docker_ctx -xf "$TMP_ARCHIVE"
                            rm -f "$TMP_ARCHIVE"
                            # 컨텍스트 점검
                            ls -la _docker_ctx | sed -n '1,120p'
                            test -f _docker_ctx/package.json || { echo "missing package.json in _docker_ctx"; exit 1; }
                            chmod -R 755 _docker_ctx
                            cp "$ENV_FILE" _docker_ctx/.env
                            
                            # 사전 pnpm 설치는 생략 (Dockerfile에서 처리)
                            ls -la _docker_ctx/.env
                            ls -lh _docker_ctx/pnpm-lock.yaml
                            TAG="${FE_IMAGE_NAME}:test-${BUILD_NUMBER}"
                            docker build -t "$TAG" --build-arg ENV=test _docker_ctx
                            '''
                            
                            sh """
                            # 기존 컨테이너 중지 및 삭제
                            TAG="${FE_IMAGE_NAME}:test-${BUILD_NUMBER}"
                            docker stop ${FE_TEST_CONTAINER} || true
                            docker rm ${FE_TEST_CONTAINER} || true
                            
                            # 새 컨테이너 실행
                            docker run -d \\
                                --name ${FE_TEST_CONTAINER} \\
                                --restart unless-stopped \\
                                --network ${APP_NETWORK_TEST} \\
                                --publish 17443:80 \\
                                "$TAG"
                            """
                        }
                    } else if (branch == 'main') {
                        withCredentials([file(credentialsId: '.env.production', variable: 'ENV_FILE')]) {
                            def tag = "${FE_IMAGE_NAME}:prod-${BUILD_NUMBER}"

                            sh '''
                            set -eux
                            # Docker 빌드 컨텍스트 준비
                            rm -rf _docker_ctx
                            mkdir -p _docker_ctx
                            SRC_DIR="."
                            if [ -d frontend-repo ]; then SRC_DIR="frontend-repo"; fi
                            TMP_ARCHIVE="$(mktemp -t ctx.XXXXXX.tar)"
                            tar -C "$SRC_DIR" --no-same-owner -cf "$TMP_ARCHIVE" --exclude=.git --exclude=_docker_ctx --exclude=.env* .
                            tar -C _docker_ctx -xf "$TMP_ARCHIVE"
                            rm -f "$TMP_ARCHIVE"
                            # 컨텍스트 점검
                            ls -la _docker_ctx | sed -n '1,120p'
                            test -f _docker_ctx/package.json || { echo "missing package.json in _docker_ctx"; exit 1; }
                            chmod -R 755 _docker_ctx
                            cp "$ENV_FILE" _docker_ctx/.env.production
                            
                            # 사전 pnpm 설치는 생략 (Dockerfile에서 처리)
                            ls -la _docker_ctx/.env.production
                            ls -lh _docker_ctx/pnpm-lock.yaml
                            TAG="${FE_IMAGE_NAME}:prod-${BUILD_NUMBER}"
                            docker build -t "$TAG" --build-arg ENV=prod _docker_ctx
                            '''
                            
                            sh """
                            # 기존 컨테이너 중지 및 삭제
                            TAG="${FE_IMAGE_NAME}:prod-${BUILD_NUMBER}"
                            docker stop ${FE_PROD_CONTAINER} || true
                            docker rm ${FE_PROD_CONTAINER} || true
                            
                            # 새 컨테이너 실행
                            docker run -d \\
                                --name ${FE_PROD_CONTAINER} \\
                                --restart unless-stopped \\
                                --network ${APP_NETWORK_PROD} \\
                                --publish 7443:80 \\
                                "$TAG"
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
                    sendMMNotify(true, buildInfo)
                    
                } else if (currentBuild.result == 'FAILURE') {
                    echo "🚨 POST: 빌드 실패 – 로그 추출 후 Mattermost 알림 전송"
                    
                    // Jenkins 내장 API로 로그 추출 (마지막 150줄)
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
                }
                
                echo "📦 Pipeline finished with status: ${currentBuild.currentResult}"
            }
        }
    }
}

// 브랜치 해석: BRANCH_NAME → TARGET_BRANCH → git
def resolveBranch() {
    if (env.BRANCH_NAME) return env.BRANCH_NAME
    if (env.TARGET_BRANCH) return env.TARGET_BRANCH
    if (env.SOURCE_BRANCH) return env.SOURCE_BRANCH
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
    def titleLine = success ? "## :jenkins7: 프론트엔드 빌드 성공 ✅"
                            : "## :angry_jenkins: 프론트엔드 빌드 실패 ❌"
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
    
    // 안전 전송
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

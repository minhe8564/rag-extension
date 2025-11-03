pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

    parameters {
        booleanParam(name: 'BUILD_QUERY_EMBEDDING', defaultValue: true, description: 'Query Embedding Service를 수동으로 빌드하고 배포하려면 체크하세요.')
        string(name: 'BRANCH_TO_BUILD', defaultValue: 'develop', description: '수동 빌드 시 기준 브랜치를 선택하세요 (develop 또는 main).')
        booleanParam(name: 'CLEANUP_ONLY', defaultValue: false, description: '오래된 컨테이너/이미지 정리만 수행')
    }

    environment {
        // Image & Container
        QUERY_EMBEDDING_IMAGE_NAME = "hebees/query-embedding"
        QUERY_EMBEDDING_CONTAINER  = "hebees-query-embedding"

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

        stage('Update uv.lock') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_QUERY_EMBEDDING == true }
                }
            }
            steps {
                sh '''
                set -eux
                # Docker 컨테이너에서 uv lock 실행 (권한 문제 회피)
                docker run --rm -v "$PWD":/app -w /app python:3.11-slim bash -c "
                    apt-get update -qq && apt-get install -y -qq curl ca-certificates >/dev/null 2>&1 && \
                    curl -fsSL https://astral.sh/uv/install.sh | sh && \
                    /root/.local/bin/uv lock && \
                    chown -R $(id -u):$(id -g) uv.lock 2>/dev/null || true
                "
                echo "uv.lock updated successfully"
                '''
            }
        }

        stage('Prepare Docker Networks') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_QUERY_EMBEDDING == true }
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
                    expression { params.BUILD_QUERY_EMBEDDING == true }
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

                    def tag = "${QUERY_EMBEDDING_IMAGE_NAME}:${env.BUILD_NUMBER}"
                    sh """
                    set -eux
                    docker build -t ${tag} .
                    """
                    env.QUERY_EMBEDDING_BUILD_TAG = tag
                }
            }
        }

        stage('Deploy Docker Container') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_QUERY_EMBEDDING == true }
                }
            }
            steps {
                withCredentials([file(credentialsId: 'query-embedding-repo.env', variable: 'QUERY_EMBEDDING_ENV_FILE')]) {
                    sh '''
                    set -eux
                    # 기존 컨테이너 종료/삭제
                    docker stop "$QUERY_EMBEDDING_CONTAINER" || true
                    docker rm "$QUERY_EMBEDDING_CONTAINER" || true

                    # 컨테이너 실행: --env-file로 환경 변수 주입
                    docker run -d \
                        --name "$QUERY_EMBEDDING_CONTAINER" \
                        --restart unless-stopped \
                        --network "$APP_NETWORK_TEST" \
                        --network "$APP_NETWORK_PROD" \
                        --network "$DB_NETWORK" \
                        --env-file "$QUERY_EMBEDDING_ENV_FILE" \
                        "$QUERY_EMBEDDING_BUILD_TAG"
                    '''
                }
            }
        }

        stage('Health Check') {
            when {
                anyOf {
                    expression { env.GITLAB_OBJECT_KIND == 'push' }
                    expression { params.BUILD_QUERY_EMBEDDING == true }
                }
            }
            steps {
                script {
                    def maxRetries = 30
                    def ok = false
                    for (int i = 0; i < maxRetries; i++) {
                        def status = sh(script: '''
                            docker run --rm --network "$APP_NETWORK_TEST" curlimages/curl:8.8.0 \
                                -fsS http://$QUERY_EMBEDDING_CONTAINER:8000/health >/dev/null
                        ''', returnStatus: true)
                        if (status == 0) { ok = true; break }
                        sleep 2
                    }
                    if (!ok) { error "Health check failed for ${QUERY_EMBEDDING_CONTAINER}" }
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
    def titleLine = success ? "## :jenkins7: Query Embedding 서비스 빌드 성공 ✅"
                            : "## :angry_jenkins: Query Embedding 서비스 빌드 실패 ❌"
    def lines = []
    if (info.mention) lines << "**작성자**: ${info.mention}"
    if (info.branch)  lines << "**대상 브랜치**: `${info.branch}`"
    if (info.commit?.msg) {
        def commitLine = info.commit?.url ? "[${info.commit.msg}](${info.commit.url})" : info.commit.msg
        lines << "**커밋**: ${commitLine}"
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


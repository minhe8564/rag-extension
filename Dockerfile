FROM node:22.10.0-alpine AS base

# pnpm 설치
RUN npm install -g pnpm
WORKDIR /app

# 의존성 파일만 먼저 복사 (레이어 캐싱 최적화)
COPY package.json pnpm-lock.yaml ./

# 의존성 설치 (lockfile이 이미 업데이트되어 있으므로 frozen-lockfile 사용)
# 만약 lockfile이 최신이 아니라면 일반 install로 자동 전환
RUN pnpm install --frozen-lockfile || pnpm install

# 소스 코드 복사 (코드 변경 시에만 이 레이어가 재빌드됨)
COPY . .

FROM base AS builder

# 빌드 모드 전달 (default=production). Jenkins에서 --build-arg MODE=development 로 변경 가능
ARG MODE=production
ENV VITE_BUILD_MODE=$MODE
RUN pnpm run build -- --mode $MODE

# Nginx를 사용한 정적 파일 서빙
FROM nginx:alpine AS production

COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

# 포트 노출
EXPOSE 80

# Nginx 실행
CMD ["nginx", "-g", "daemon off;"]

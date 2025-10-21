FROM node:22.10.0-alpine AS base

# pnpm 설치
RUN npm install -g pnpm
WORKDIR /app

# 의존성 파일만 먼저 복사 (레이어 캐싱 최적화)
COPY package.json pnpm-lock.yaml ./

# 의존성 설치 (package.json이 변경될 때만 재실행)
RUN pnpm install --frozen-lockfile

# 소스 코드 복사 (코드 변경 시에만 이 레이어가 재빌드됨)
COPY . .

FROM base AS builder

RUN pnpm run build

# Nginx를 사용한 정적 파일 서빙
FROM nginx:alpine AS production

COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

# 포트 노출
EXPOSE 80

# Nginx 실행
CMD ["nginx", "-g", "daemon off;"]

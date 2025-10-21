<<<<<<< HEAD
FROM node:22-alpine AS base
=======
FROM node:22.10.0-alpine AS base
>>>>>>> ec401138e455b8322d634d7c0fca76202c4ad7a8

RUN npm install -g pnpm
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# 소스 코드 복사
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

# Stage 1: build static web assets
FROM node:20-alpine AS web-build

WORKDIR /app
COPY src/mermaid_diagram/export_options.json ./src/mermaid_diagram/export_options.json
COPY web/package.json web/package-lock.json ./web/
WORKDIR /app/web
RUN npm ci
COPY web/ ./
RUN npm run build

# Stage 2: serve with nginx
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=web-build /app/web/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK CMD wget -qO- http://localhost/ || exit 1

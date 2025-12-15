controller:
  autoscaling:
    enabled: true
    minReplicas: 1
    maxReplicas: 3
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 70
  resources:
    requests:
      cpu: 200m
      memory: 256Mi
  service:
    annotations:
      service.beta.kubernetes.io/aws-load-balancer-type: external
      service.beta.kubernetes.io/aws-load-balancer-scheme: internet-facing
      service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: ip
      service.beta.kubernetes.io/aws-load-balancer-backend-protocol: tcp
      service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"
      service.beta.kubernetes.io/aws-load-balancer-ssl-cert: ${lb_acm_certificate_arn}
      service.beta.kubernetes.io/aws-load-balancer-proxy-protocol: "*"
      service.beta.kubernetes.io/aws-load-balancer-attributes: load_balancing.cross_zone.enabled=true
    targetPorts:
      https: http
  config:
    # NLB에서 Proxy Protocol(v2) 사용 시 반드시 활성화
    use-proxy-protocol: "true"
    real-ip-header: "proxy_protocol"
    # Proxy Protocol에서 실제 클라이언트 IP를 추출하기 위한 신뢰할 수 있는 IP 범위 설정
    # Proxy Protocol을 사용할 때는 모든 IP를 신뢰하도록 설정 (NLB가 Proxy Protocol을 통해 실제 IP를 전달)
    set-real-ip-from: "0.0.0.0/0"
    use-forwarded-headers: "true"
    # Proxy Protocol에서 실제 클라이언트 IP 추출을 위한 설정
    compute-full-forwarded-for: "true"
    forwarded-for-header: "X-Forwarded-For"
    # SnippetAnnotation등을 사용하기 위해서는 이제 위험 레벨을 Critical로 설정해야 합니다
    annotations-risk-level: "Critical"
  allowSnippetAnnotations: true
  # ingeress state의 ADDRESS 값이 Node IP가 아닌 ELB의 주소가 찍히도록합니다
  # 만약 false인 경우 External-dns와 같은 외부 서비스가 원하는대로 레코드를 등록하지 못합니다
  publishService:
    enabled: true

---


providers:
  kubernetesIngress:
    publishedService:
      enabled: true
  file:
    enabled: true
    content: |
      ${providers_file_content}
  # kubernetesGateway:
  #   enabled: true
service:
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: external
    service.beta.kubernetes.io/aws-load-balancer-scheme: internet-facing
    service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: ip
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: tcp
    service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: ${acm_certificate_arn}
    service.beta.kubernetes.io/aws-load-balancer-proxy-protocol: "*"
    service.beta.kubernetes.io/aws-load-balancer-attributes: load_balancing.cross_zone.enabled=true
    # Traefik 서비스 자체는 external-dns에서 제외 (CNAME 루프 방지)
    external-dns.alpha.kubernetes.io/exclude: "true"
ports:
  web:
    proxyProtocol:
      trustedIPs:
        - ${vpc_cidr}
    forwardedHeaders:
      trustedIPs:
        - ${vpc_cidr}
    middlewares:
      - forwardedHeader@file
  websecure:
    targetPort: web
    tls:
      enabled: false
  traefik:
    expose:
      default: true
additionalArguments:
  - "--api.insecure=true"

logs:
  access:
    enabled: true
    format: json
resources:
  requests:
    cpu: 200m
    memory: 256Mi
autoscaling:
  enabled: true
  minReplicas: 1
  maxReplicas: 3
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 70

---
http:
  middlewares:

    # -----------------------------
    # Forwarded Header (NLB에서 Proxy Protocol 사용 시)
    # -----------------------------
    forwardedHeader:
      headers:
        customRequestHeaders:
          X-Forwarded-Proto: "https"
          X-Forwarded-Port: "443"

    # -----------------------------
    # HTTPS 강제 리다이렉트
    # -----------------------------
    https-redirect:
      redirectScheme:
        scheme: https
        permanent: true

    # -----------------------------
    # 보안 + 캐시 방지 헤더
    # (NGINX configuration-snippet 대체)
    # -----------------------------
    security-headers:
      headers:
        contentTypeNosniff: true
        frameDeny: true
        browserXssFilter: true

        customResponseHeaders:
          Pragma: "no-cache"
          Cache-Control: "max-age=0, no-store, no-cache, must-revalidate"

    # -----------------------------
    # CORS 설정
    # -----------------------------
    cors:
      headers:
        addVaryHeader: true
        accessControlAllowMethods:
          - GET
          - POST
          - HEAD
          - OPTIONS
        accessControlAllowHeaders:
          - X-Forwarded-For
        # accessControlAllowCredentials: true
        # 정규식으로 패턴 매칭 (*.seungdobae.com 모든 서브도메인 허용)
        # Traefik CORS 미들웨어는 accessControlAllowOriginList 또는 accessControlAllowOriginListRegex 중 하나가 필수
        accessControlAllowOriginList:
          - "*" 
        # accessControlAllowOriginListRegex:
        #   - "^https://.*\\.seungdobae\\.com$"
        #   - "^https://seungdobae\\.com$"

    # -----------------------------
    # 공통 미들웨어 체인
    # -----------------------------
    app-chain:
      chain:
        middlewares:
          - https-redirect
          - security-headers
          - cors

  # -----------------------------
  # Backend timeout (proxy read/send)
  # -----------------------------
  serversTransports:
    backend-timeout:
      forwardingTimeouts:
        responseHeaderTimeout: 60s
        idleConnTimeout: 60s

---

# ingress-nginx > Traefik 옮기기

이 문서는 Kubernetes NGINX Ingress Controller에서 Traefik으로 마이그레이션하는 과정에서 겪은 문제들과 해결 방법을 정리한 가이드입니다.

## 📋 목차

- [개요](#개요)
- [주요 변경사항](#주요-변경사항)
- [설정 매핑](#설정-매핑)
- [실제 사용된 미들웨어 설정](#실제-사용된-미들웨어-설정)
- [주의사항 및 트러블슈팅](#주의사항-및-트러블슈팅)
- [참고 자료](#참고-자료)

## 개요

NGINX Ingress Controller는 2026년 3월에 공식적으로 지원이 종료됩니다. Traefik은 NGINX 어노테이션을 지원하여 마이그레이션을 용이하게 하지만, 일부 동작 방식의 차이로 인해 주의가 필요합니다.

## 주요 변경사항

### 1. Ingress 리소스 → IngressRoute

NGINX는 표준 Kubernetes Ingress 리소스를 사용하지만, Traefik은 IngressRoute CRD를 사용합니다.

**NGINX (Ingress):**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    nginx.ingress.kubernetes.io/affinity: cookie
spec:
  ingressClassName: nginx
  rules:
    - host: nginx.seungdobae.com
```

**Traefik (IngressRoute):**
```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: app-ingressroute
spec:
  entryPoints:
    - web
  routes:
    - match: Host(`traefik.seungdobae.com`)
      kind: Rule
      middlewares:
        - name: security-headers@file
        - name: cors@file
      sticky:
        cookie:
          name: route
          httpOnly: true
          secure: true
          sameSite: lax
```

### 2. 어노테이션 → 미들웨어

NGINX는 Ingress 어노테이션으로 설정하지만, Traefik은 별도의 Middleware 리소스를 사용합니다.

## 설정 매핑

### Session Affinity (Sticky Session)

| NGINX | Traefik |
|-------|---------|
| `nginx.ingress.kubernetes.io/affinity: cookie` | `sticky.cookie` (IngressRoute spec) |
| `nginx.ingress.kubernetes.io/session-cookie-name: route` | `sticky.cookie.name: route` |
| `nginx.ingress.kubernetes.io/session-cookie-samesite: "Lax"` | `sticky.cookie.sameSite: lax` |
| `nginx.ingress.kubernetes.io/session-cookie-secure: "true"` | `sticky.cookie.secure: true` |
| `nginx.ingress.kubernetes.io/session-cookie-httponly: "true"` | `sticky.cookie.httpOnly: true` |
| `nginx.ingress.kubernetes.io/session-cookie-hash: sha1` | 자동 처리 (Traefik이 내부적으로 처리) |

**실제 설정 (values_traefik.yaml):**
```yaml
ingressRoute:
  enabled: true
  entryPoints:
    - web
  routes:
    - match: Host(`traefik.seungdobae.com`)
      kind: Rule
      middlewares:
        - name: security-headers@file
        - name: cors@file
      sticky:
        cookie:
          name: route
          httpOnly: true
          secure: true
          sameSite: lax
```

### CORS 설정

| NGINX | Traefik |
|-------|---------|
| `nginx.ingress.kubernetes.io/enable-cors: "true"` | `cors` 미들웨어 |
| `nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, HEAD, OPTIONS"` | `accessControlAllowMethods` |
| `nginx.ingress.kubernetes.io/cors-allow-headers: X-Forwarded-For` | `accessControlAllowHeaders` |

**실제 설정 (Traefik File Provider):**
```yaml
http:
  middlewares:
    cors:
      headers:
        addVaryHeader: true
        accessControlAllowMethods:
          - GET
          - POST
          - HEAD
          - OPTIONS
        accessControlAllowHeaders:
          - X-Forwarded-For
        accessControlAllowOriginList:
          - "*"
```

### Security Headers

| NGINX | Traefik |
|-------|---------|
| `nginx.ingress.kubernetes.io/configuration-snippet` | `headers` 미들웨어 |
| `add_header X-Content-Type-Options nosniff;` | `contentTypeNosniff: true` |
| `add_header X-Frame-Options DENY;` | `frameDeny: true` |
| `add_header X-XSS-Protection "1;mode=block";` | `browserXssFilter: true` |
| `add_header Pragma "no-cache";` | `customResponseHeaders.Pragma` |
| `add_header Cache-Control "max-age=0, no-store, no-cache, must-revalidate";` | `customResponseHeaders.Cache-Control` |

**실제 설정 (Traefik File Provider):**
```yaml
http:
  middlewares:
    security-headers:
      headers:
        contentTypeNosniff: true
        frameDeny: true
        browserXssFilter: true
        customResponseHeaders:
          Pragma: "no-cache"
          Cache-Control: "max-age=0, no-store, no-cache, must-revalidate"
```

### Proxy Timeout

| NGINX | Traefik |
|-------|---------|
| `nginx.ingress.kubernetes.io/proxy-read-timeout: "60"` | `serversTransports.backend-timeout.forwardingTimeouts.responseHeaderTimeout: 60s` |
| `nginx.ingress.kubernetes.io/proxy-send-timeout: "60"` | `serversTransports.backend-timeout.forwardingTimeouts.idleConnTimeout: 60s` |

## 실제 사용된 미들웨어 설정

현재 프로젝트에서 실제로 사용 중인 Traefik File Provider 설정입니다:

```yaml
http:
  middlewares:
    # Forwarded Header (NLB에서 Proxy Protocol 사용 시)
    forwardedHeader:
      headers:
        customRequestHeaders:
          X-Forwarded-Proto: "https"
          X-Forwarded-Port: "443"

    # HTTPS 강제 리다이렉트
    https-redirect:
      redirectScheme:
        scheme: https
        permanent: true

    # 보안 + 캐시 방지 헤더
    security-headers:
      headers:
        contentTypeNosniff: true
        frameDeny: true
        browserXssFilter: true
        customResponseHeaders:
          Pragma: "no-cache"
          Cache-Control: "max-age=0, no-store, no-cache, must-revalidate"

    # CORS 설정
    cors:
      headers:
        addVaryHeader: true
        accessControlAllowMethods:
          - GET
          - POST
          - HEAD
          - OPTIONS
        accessControlAllowHeaders:
          - X-Forwarded-For
        accessControlAllowOriginList:
          - "*"
```

## 주의사항 및 트러블슈팅

### 1. CORS 헤더가 보이지 않는 문제

**문제:**
- NGINX는 `enable-cors: true` 설정 시 항상 CORS 헤더를 응답에 추가합니다.
- Traefik CORS 미들웨어는 **실제 CORS 요청**이 있을 때만 헤더를 추가합니다.

**원인:**
Traefik의 CORS 미들웨어는 브라우저가 실제로 CORS 요청을 보낼 때만 동작합니다. 같은 origin에서 요청하면 CORS 헤더가 보이지 않는 것이 정상 동작입니다.

**해결 방법:**
1. **테스트 방법:** 브라우저 개발자 도구에서 다른 origin으로 요청하거나, curl로 `Origin` 헤더를 포함한 요청을 보냅니다.
   ```bash
   curl -H "Origin: https://example.com" \
        -H "Access-Control-Request-Method: GET" \
        -v https://traefik.seungdobae.com
   ```

2. **항상 헤더가 보이게 하려면:** Headers 미들웨어를 사용하여 CORS 헤더를 직접 추가합니다.
   ```yaml
   security-headers:
     headers:
       customResponseHeaders:
         "Access-Control-Allow-Origin": "*"
         "Access-Control-Allow-Methods": "GET, POST, HEAD, OPTIONS"
         "Access-Control-Allow-Headers": "X-Forwarded-For"
   ```

**참고:** [Traefik 공식 문서 - NGINX Ingress 제한사항](https://doc.traefik.io/traefik/reference/routing-configuration/kubernetes/ingress-nginx/#limitations)

### 2. route 쿠키 값이 다른 이유

**문제:**
- NGINX: `route` 쿠키 값이 `1765529581.422.299.619556|9f0ad6c0362b933ed31304da45a65f6c` 형식
- Traefik: `route` 쿠키 값이 `43c2d8ffd595c1e1` 형식

**원인:**
각 컨트롤러가 서로 다른 알고리즘을 사용하여 쿠키 값을 생성합니다:
- **NGINX:** 백엔드 서비스의 IP:Port를 기반으로 해시 값을 생성 (`백엔드해시.가중치.인덱스.체크섬|SHA1해시`)
- **Traefik:** 자체 알고리즘으로 백엔드 식별자를 생성 (더 짧고 간단한 형식)

**해결:**
이것은 정상적인 동작입니다. 각 컨트롤러가 독립적으로 동작하며, 모두 같은 목적(세션 어피니티)을 달성합니다.

### 3. 미들웨어 적용 순서

Traefik에서 미들웨어는 선언된 순서대로 적용됩니다. IngressRoute에서 미들웨어 순서를 주의하세요:

```yaml
routes:
  - match: Host(`traefik.seungdobae.com`)
    middlewares:
      - name: security-headers@file  # 1순위
      - name: cors@file              # 2순위
```

### 4. Terraform으로 미들웨어 관리

현재 프로젝트에서는 Traefik File Provider를 통해 미들웨어를 관리하고 있습니다. Terraform으로 관리하려면:

```hcl
resource "traefik_middleware" "cors" {
  name      = "cors"
  namespace = "default"

  cors {
    allow_origin_list = ["*"]
    allow_methods     = ["GET", "POST", "HEAD", "OPTIONS"]
    allow_headers     = ["X-Forwarded-For"]
  }
}
```

자세한 내용은 `example-traefik-middleware.md` 파일을 참고하세요.

## 참고 자료

- [Traefik 공식 문서 - NGINX Ingress 제한사항](https://doc.traefik.io/traefik/reference/routing-configuration/kubernetes/ingress-nginx/#limitations)
- [Traefik Middleware 문서](https://doc.traefik.io/traefik/middlewares/overview/)
- [NGINX to Traefik Migration Guide](https://doc.traefik.io/traefik/migrate/nginx-ingress-to-traefik/)
- [Terraform Traefik Provider 문서](https://registry.terraform.io/providers/traefik/traefik/latest/docs)

---
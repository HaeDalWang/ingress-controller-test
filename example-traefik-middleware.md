# Traefik Middleware Terraform File Provider 예제

이 문서는 현재 Helm 차트에서 사용 중인 Traefik Middleware 구성을 Terraform Traefik File Provider로 관리하기 위한 예제입니다.

## 개요

Traefik Middleware는 Helm 차트에서 관리하지 않고, Terraform의 Traefik File Provider를 통해 별도로 관리됩니다.

## 필요한 Middleware

현재 적용 중인 Middleware는 다음과 같습니다:

1. **Sticky Middleware** - Session Affinity (Cookie 기반)
2. **CORS Middleware** - CORS 설정
3. **Headers Middleware** - Security Headers

## Terraform 구성 예제

### 1. Sticky Middleware (Session Affinity)

```hcl
resource "traefik_middleware" "sticky" {
  name      = "ingress-echo-sticky"
  namespace = "default"  # 실제 네임스페이스로 변경

  sticky {
    cookie {
      name     = "route"
      secure   = true
      http_only = true
      same_site = "Lax"
    }
  }
}
```

**nginx와의 매핑:**
- `nginx.ingress.kubernetes.io/affinity: cookie`
- `nginx.ingress.kubernetes.io/session-cookie-name: route`
- `nginx.ingress.kubernetes.io/session-cookie-samesite: "Lax"`
- `nginx.ingress.kubernetes.io/session-cookie-secure: "true"`
- `nginx.ingress.kubernetes.io/session-cookie-httponly: "true"`
- `nginx.ingress.kubernetes.io/session-cookie-hash: sha1` (Traefik은 자동 처리)

### 2. CORS Middleware

```hcl
resource "traefik_middleware" "cors" {
  name      = "ingress-echo-cors"
  namespace = "default"  # 실제 네임스페이스로 변경

  cors {
    allow_origin_list = ["*"]
    allow_methods     = ["GET", "POST", "HEAD", "OPTIONS"]
    allow_headers     = ["X-Forwarded-For", "Content-Type", "Authorization"]
    expose_headers    = ["X-Forwarded-For"]
    max_age           = 86400
  }
}
```

**nginx와의 매핑:**
- `nginx.ingress.kubernetes.io/enable-cors: "true"`
- `nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, HEAD, OPTIONS"`
- `nginx.ingress.kubernetes.io/cors-allow-headers: X-Forwarded-For`

### 3. Headers Middleware (Security Headers)

```hcl
resource "traefik_middleware" "headers" {
  name      = "ingress-echo-headers"
  namespace = "default"  # 실제 네임스페이스로 변경

  headers {
    custom_response_headers = {
      "X-Content-Type-Options" = "nosniff"
      "Pragma"                  = "no-cache"
      "Cache-Control"          = "max-age=0, no-store, no-cache, must-revalidate"
      "X-XSS-Protection"       = "1;mode=block"
      "X-Frame-Options"        = "DENY"
    }
  }
}
```

**nginx와의 매핑:**
- `nginx.ingress.kubernetes.io/configuration-snippet`의 다음 헤더들:
  - `add_header X-Content-Type-Options nosniff;`
  - `add_header Pragma "no-cache";`
  - `add_header Cache-Control "max-age=0, no-store, no-cache, must-revalidate";`
  - `more_set_headers "X-Xss-Protection: 1;mode=block";`
  - `more_set_headers "X-Frame-Options: DENY";`

### 4. 전체 예제 (통합)

```hcl
# Sticky Middleware
resource "traefik_middleware" "ingress_echo_sticky" {
  name      = "ingress-echo-sticky"
  namespace = "default"

  sticky {
    cookie {
      name     = "route"
      secure   = true
      http_only = true
      same_site = "Lax"
    }
  }
}

# CORS Middleware
resource "traefik_middleware" "ingress_echo_cors" {
  name      = "ingress-echo-cors"
  namespace = "default"

  cors {
    allow_origin_list = ["*"]
    allow_methods     = ["GET", "POST", "HEAD", "OPTIONS"]
    allow_headers     = ["X-Forwarded-For", "Content-Type", "Authorization"]
    expose_headers    = ["X-Forwarded-For"]
    max_age           = 86400
  }
}

# Headers Middleware
resource "traefik_middleware" "ingress_echo_headers" {
  name      = "ingress-echo-headers"
  namespace = "default"

  headers {
    custom_response_headers = {
      "X-Content-Type-Options" = "nosniff"
      "Pragma"                  = "no-cache"
      "Cache-Control"          = "max-age=0, no-store, no-cache, must-revalidate"
      "X-XSS-Protection"       = "1;mode=block"
      "X-Frame-Options"        = "DENY"
    }
  }
}
```

## Ingress에서 Middleware 참조

Helm 차트의 Ingress 리소스에서 다음과 같이 Middleware를 참조합니다:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-echo
  annotations:
    traefik.ingress.kubernetes.io/middlewares: ingress-echo-sticky,ingress-echo-cors,ingress-echo-headers
    traefik.ingress.kubernetes.io/redirect-to-https: "true"
spec:
  ingressClassName: traefik
  # ...
```

또는 Terraform으로 IngressRoute를 사용하는 경우:

```hcl
resource "traefik_ingress_route" "ingress_echo" {
  name      = "ingress-echo"
  namespace = "default"

  entry_points = ["web", "websecure"]

  route {
    match = "Host(`traefik.seungdobae.com`)"
    
    middlewares = [
      traefik_middleware.ingress_echo_sticky.name,
      traefik_middleware.ingress_echo_cors.name,
      traefik_middleware.ingress_echo_headers.name,
    ]

    kind  = "Rule"
    services = [{
      name = "ingress-echo"
      port = 8001
    }]
  }

  tls {
    secret_name = "ingress-echo-tls"  # TLS 인증서가 있는 경우
  }
}
```

## 주의사항

1. **네임스페이스**: 실제 배포 환경의 네임스페이스로 변경해야 합니다.
2. **Middleware 이름**: Helm 차트의 `fullname`과 일치하도록 설정해야 합니다.
3. **순서**: Middleware는 선언된 순서대로 적용됩니다.
4. **Cookie 플래그 수정**: nginx의 `proxy_cookie_flags JSESSIONID SameSite=Lax Secure HttpOnly`는 Traefik Middleware로 직접 구현하기 어렵습니다. 필요시 별도 Middleware나 애플리케이션 레벨에서 처리해야 합니다.

## 참고

- [Traefik Middleware 문서](https://doc.traefik.io/traefik/middlewares/overview/)
- [Terraform Traefik Provider 문서](https://registry.terraform.io/providers/traefik/traefik/latest/docs)


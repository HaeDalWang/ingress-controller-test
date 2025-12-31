## EnvoyGateway - Gateway 사용법

핵심 차이점

- **책임 분리 (Routing vs Policy)**
    - `HTTPRoute`: 호스트, 경로, **보안 헤더(ResponseHeaderModifier)** 등 **표준 L7 라우팅 흐름**을 정의합니다.
    - `SecurityPolicy`: CORS, JWT인증 등 **보안 및 접근 제어**를 담당합니다. (※ v1.6 기준 `headers` 필드 미지원)
    - `BackendTrafficPolicy`: 타임아웃, 세션 유지(Sticky Cookie), 요청 본문 크기 제한 등 **업스트림 트래픽 제어**를 담당합니다.
- **TLS 관리 방식**
    - `Gateway Listener`에서 인증서를 정의하며, 애플리케이션의 `HTTPRoute`는 비즈니스 로직에만 집중합니다.

**Traefik vs Envoy Gateway 기능 비교**

| **기능 분류** | **Traefik (Middleware/CRD)** | **Envoy Gateway (CRD/Filter)** | **주요 차이점** |
| --- | --- | --- | --- |
| **HTTPS 리다이렉트** | `Middleware` (redirectScheme) | `HTTPRoute` 내 `RequestRedirect` 필터 | 별도 리소스 없이 라우팅 규칙에 내장됨 |
| **CORS 설정** | `Middleware` (cors) | `SecurityPolicy` (spec.cors) | 보안 정책 리소스로 통합 관리됨 |
| **보안 헤더** | `Middleware` (headers) | `HTTPRoute` 내 `ResponseHeaderModifier` 필터 | ※ SecurityPolicy가 아닌 HTTPRoute filter로 설정 |
| **속도 제한** | `Middleware` (rateLimit) | `BackendTrafficPolicy` (spec.rateLimit) | 로컬 및 Redis 기반 글로벌 제한 지원 |
| **인증 (JWT/OIDC)** | `ForwardAuth` 또는 Enterprise | `SecurityPolicy` (spec.jwt, spec.oidc) | 외부 컴포넌트 없이 자체 필터 |
| **세션 유지** | `Service` Annotation / `IngressRoute` sticky | `BackendTrafficPolicy` (spec.loadBalancer.consistentHash.cookie) | 쿠키 기반 Sticky Session, **ttl 설정 필수** |
| **요청 타임아웃** | `Middleware` (retry) | `BackendTrafficPolicy` (spec.timeout.http.requestTimeout) | 업스트림 요청 타임아웃 설정 |
| **요청 본문 크기 제한** | N/A (nginx annotation) | `BackendTrafficPolicy` (spec.requestBuffer.limit) | 초과 시 HTTP 413 반환 |
| **회로 차단** | `Middleware` (circuitBreaker) | `BackendTrafficPolicy` (spec.circuitBreaker) | 서비스 가용성을 위한 상세 수치 설정 가능 |

> ⚠️ **주의사항 (v1.6 기준)**
> - SecurityPolicy의 `spec.headers` 필드는 지원되지 않음 → HTTPRoute의 ResponseHeaderModifier 사용
> - Sticky Cookie 자동 생성을 위해 `cookie.ttl` 설정 필수
> - CORS 헤더는 Cross-Origin 요청에만 응답 (Same-Origin에서는 안 보임)

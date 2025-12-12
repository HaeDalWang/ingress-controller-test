
``` yaml
ingress:
  enabled: true
  annotations:
    nginx.ingress.kubernetes.io/affinity: cookie
    nginx.ingress.kubernetes.io/session-cookie-name: route
    nginx.ingress.kubernetes.io/session-cookie-samesite: "Lax"
    nginx.ingress.kubernetes.io/session-cookie-secure: "true"
    nginx.ingress.kubernetes.io/session-cookie-httponly: "true"
    nginx.ingress.kubernetes.io/session-cookie-hash: sha1
    nginx.ingress.kubernetes.io/cors-allow-headers: X-Forwarded-For
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/enable-cors: "true"
    nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, HEAD, OPTIONS"
    #(if need)nginx.ingress.kubernetes.io/proxy-body-size: "500m"
    #(if need)nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/configuration-snippet: |
       add_header X-Content-Type-Options nosniff;
       add_header Pragma "no-cache";
       add_header Cache-Control "max-age=0, no-store, no-cache, must-revalidate";
       proxy_cookie_flags JSESSIONID SameSite=Lax Secure HttpOnly;
       more_set_headers "X-Xss-Protection: 1;mode=block";
       more_set_headers "X-Frame-Options: DENY";  

       ## url redirect
       #if ($request_uri = "/") {
       #  return 301 $scheme://$host/redirect_url;
       #}
       ## domain redirect
       #set $primary_domain "www.yumin.org";
       #if ($host != $primary_domain) {
       #  return 301 $scheme://$primary_domain$request_uri;
       #}
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60" #default 60
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60" #default 60
```
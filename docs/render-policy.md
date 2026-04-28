# Render Policy Boundary

Render policy is enforced before web reports are built.

Default web requests do not render draft, build-blocked, or promotion-blocked claims. A direct claim request for a hidden claim returns the generic `404 Not Found` response for anonymous requests. The response body does not include the claim id, statement, value, provenance, or a redacted claim shape.

Neighborhood and concept reports are policy-relative. Hidden claims are absent from default graph endpoints, node lists, edge lists, tables, and concept counts. Administrative opt-in flags such as `include_blocked` can widen the policy, but the default posture is non-disclosure.

Malformed concept full-text search queries return `400 Invalid Search Query`.

`pks web` binds to loopback by default. Serving on a public interface such as `0.0.0.0` requires `--insecure` and prints a warning because the web UI has no authentication layer.

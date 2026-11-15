# ota-extract

Small Rust helper around `unpayload` 0.1.2. It reads `payload.bin` from a
local full-OTA zip, or opens an OTA URL with HTTP range requests, and
writes selected partitions.

```sh
# local zip (central directory must be present)
cargo run --release -- OTA.zip out recovery vendor odm

# URL: download only the ranges the selected partitions need
cargo run --release --bin fetch-url -- 'https://.../ota.zip?auth=...' out recovery
```

`fetch-url` needs a direct HTTP(S) URL. Share links that require a login
or a client app (QQ 闪传, Quark web without a session) do not work; resolve
them to a signed CDN URL first.

`extract-at` is for a partially downloaded zip whose `payload.bin` starts
at a known byte offset:

```sh
cargo run --release --bin extract-at -- partial.zip 61 out recovery
```

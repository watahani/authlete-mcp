# GitHub Actions Parallel Test Investigation (2025-10-09)

## Context

- Branch / PR: `reproduce-ci-parallel-failure` (PR #41 "Restore parallel GitHub Actions test matrix")
- Motivation: Re-enabling matrix parallelism on `.github/workflows/test.yml` intermittently fails during integration tests with real Authlete credentials.
- Primary failure signature (GitHub Actions run `18349467497`, job `test (3.12)`, commit `69afbbe`):
  - `Authlete API Error: [A457101] (/client/create) Function requires access rights ([CREATE_CLIENT]) for service (3350485293), access token does not have sufficient access.`
  - Service creation via IdP API returned 200 immediately before the 403.

## What was already done

1. Added instrumentation commits (`04e68ff`, `50ae6bb`, `620e7d5`) to log token hashes, timings, and stream pytest stdout (`-s`).
2. Temporarily reinstated `strategy.max-parallel: 1` to unblock CI while continuing investigation.
3. Introduced local load-test script (`scripts/load_test_authlete.py`) to explore rate limiting (documented in `docs/load_test_results_2025-10-08.md`).

## Findings today

- **GitHub Actions logs**
  - Re-downloaded failing job `52265145463` to confirm the sequence: service created (HTTP 200), immediate `client/create` returned 403 with `[CREATE_CLIENT]` right missing.
  - Other matrix legs (`3.10`, `3.11`) passed in the same run, reinforcing a race/timing issue rather than missing permissions globally.

- **Local reproduction attempts**
  - Ran `test_client_secret_operations_with_service_api_key` concurrently (2–3 workers) against the real `.env` credentials — no 403s observed.
  - Stress script (`stress-service-*`) performed 30 rapid create/delete client cycles without failures.
  - Full integration suite run concurrently (2 workers, Python 3.10) surfaced DuckDB read contention in search tests but still no Authlete 403.
  - Attempted mixed Python versions (3.10/3.11/3.12) concurrently; `uv` reused `.venv`, causing package resolution noise. Needs isolated envs to finish the experiment properly.

- **Service inspection**
  - `service/get/` responses lack an `accessRights` field; organisation token rights cannot be confirmed directly via current API calls.
  - Debug logging shows service deletions succeeding immediately after tests, so cleanup is timely.
  - The IdP `POST /api/introspect` endpoint should expose access-right details for a token; the current sandbox returns HTTP 404 (`No static resource api/introspect`), so we need to confirm the correct path or required configuration with Authlete support.

## Mitigation implemented

- Added a shared retry layer (configurable via `AUTHLETE_API_MAX_RETRIES`, `AUTHLETE_API_RETRY_BACKOFF_SECONDS`, and `AUTHLETE_API_RETRY_ERROR_CODES`) across all Authlete API helpers. The MCP server now retries `[A457101]` and transient 5xx/429 responses automatically.
- Introduced unit coverage to ensure the retry triggers only for configured errors and leaves other HTTP failures unchanged.
- Verified the behaviour by running three parallel copies of `tests/test_client_operations.py::test_client_secret_operations_with_service_api_key`; no `[A457101]` errors surfaced and logs show potential retry warning hooks ready for CI diagnostics.

## Current hypothesis

Authlete may apply organisation-token access rights to freshly created services asynchronously. Under higher load (three matrix jobs creating services simultaneously), propagation occasionally lags enough for the immediate `client/create` call to observe stale rights, yielding `[A457101]`. Sequential or lightly loaded scenarios do not show the issue, matching observed behaviour.

## Next steps

1. Re-enable CI parallelism temporarily (remove `max-parallel`) with instrumentation + `LOG_LEVEL=DEBUG` to capture updated diagnostics from a fresh failure (token hashes already masked).
2. Monitor the new retry/backoff behaviour under CI load; adjust `AUTHLETE_API_MAX_RETRIES` / `AUTHLETE_API_RETRY_BACKOFF_SECONDS` / `AUTHLETE_API_RETRY_ERROR_CODES` if failures persist.
3. Explore IdP endpoints for explicit access-right polling (e.g., `/api/service/accessright/get` if available) to convert the heuristic retry into a readiness check.
4. Investigate DuckDB locking separately before restoring full parallelism — concurrent search tests failed locally.

## Open questions

- Does Authlete provide an API to enumerate organisation access rights per service to validate readiness explicitly?
- What delay/backoff (e.g., 1–2 seconds, up to 3 attempts) balances CI reliability with run time?
- Should the cleanup job be adjusted to avoid overlapping with in-flight runs once parallelism is restored?

---

# GitHub Actions 並列テスト調査メモ (日本語要約)

## 背景

- 対象ブランチ / PR: `reproduce-ci-parallel-failure`（PR #41「Restore parallel GitHub Actions test matrix」）
- 目的: `.github/workflows/test.yml` でテストマトリクスの並列実行を再有効化すると、実トークンを使う統合テストが断続的に失敗する原因を突き止める。
- 代表的な失敗ログ（ワークフロー `18349467497`、ジョブ `test (3.12)`、コミット `69afbbe`）:
  - `Authlete API Error: [A457101] (/client/create) Function requires access rights ([CREATE_CLIENT]) for service (3350485293), access token does not have sufficient access.`
  - 403 が発生する直前の IdP API `service` 呼び出しは 200 を返しており、サービス作成自体は成功している。

## これまでの対応

1. トークンハッシュや処理時間を記録し、pytest を `-s` で標準出力に流す計測コミット（`04e68ff`, `50ae6bb`, `620e7d5`）を追加。
2. 調査継続の間は CI を通すために一時的に `strategy.max-parallel: 1` を設定。
3. レートリミットの影響を確認するためのローカル負荷試験スクリプト（`scripts/load_test_authlete.py`）を作成し、結果を `docs/load_test_results_2025-10-08.md` に記録。

## 本日の調査結果

- **GitHub Actions ログ再確認**
  - 失敗ジョブ `52265145463` を再取得し、サービス作成 (HTTP 200) 直後の `client/create` が `[CREATE_CLIENT]` 権限不足で 403 を返すことを再確認。
  - 同一ラン内の他ジョブ（Python 3.10 と 3.11）は成功しており、権限設定の永久的欠落ではなく、短時間の整合性ズレが疑われる。

- **ローカルでの再現試験**
  - `.env` に設定された実トークンを使い、`test_client_secret_operations_with_service_api_key` を 2〜3 並列で実行しても 403 は再現せず。
  - サービス・クライアントを連続 30 回作成/削除するストレス試験 (`stress-service-*`) でも失敗なし。
  - 統合テスト一式を 2 並列 (Python 3.10) で走らせたところ、DuckDB の読み取りロック競合による検索テスト失敗は発生したが、Authlete 側の 403 は発生せず。
  - Python バージョン混在 (3.10/3.11/3.12) での並列試行も検討したが、`uv` が同一 `.venv` を共有するためパッケージ解決の問題が発生。別仮想環境を分ける必要あり。

- **サービス状態の観察**
  - `service/get/` のレスポンスには `accessRights` が含まれず、権限伝播の状態を API から直接確認できなかった。
  - ログ上はテスト終了時にサービス削除が即座に成功しており、クリーンアップは正常に機能している。
  - 追加調査が必要な場合は IdP の `POST /api/introspect` で組織トークンを検査できる想定だが、現状のサンドボックスでは 404 (`No static resource api/introspect`) が返るため、正しいエンドポイント／設定を Authlete 側に確認する必要がある。

## 対応済みの緩和策

- Authlete API ヘルパー全体に共通のリトライ処理を追加（環境変数 `AUTHLETE_API_MAX_RETRIES`、`AUTHLETE_API_RETRY_BACKOFF_SECONDS`、`AUTHLETE_API_RETRY_ERROR_CODES` で調整可能）。`[A457101]` や 429/5xx を自動再試行し、権限伝播の遅延を吸収。
- 上記リトライが限定的に発火することを保証するユニットテストを追加し、他の HTTP エラーは従来通り即時エラーとなることを確認。
- `tests/test_client_operations.py::test_client_secret_operations_with_service_api_key` を 3 並列で実行し、リトライ導入後も `[A457101]` が発生しないことを確認（必要に応じてログにリトライ警告が出力される）。

## 現時点の仮説

サービス作成直後に組織トークンのアクセス権が Authlete 側で非同期適用されており、高負荷（並列ジョブが同時にサービスを作成）時に権限伝播が間に合わないケースがあると考えられる。その結果、直後の `client/create` が古い権限状態を参照し `[A457101]` を返す。一方、順次実行や低負荷では問題が顕在化しない。

## 次のアクション案

1. 計測付きの現行コードで一度 `max-parallel` を外し、`LOG_LEVEL=DEBUG` を有効化した状態で GitHub Actions を再実行し、新しい失敗ログを取得（トークンハッシュ等は既にマスク済み）。
2. 追加したリトライ処理が CI 上で有効に機能するか観測し、必要に応じて `AUTHLETE_API_MAX_RETRIES` / `AUTHLETE_API_RETRY_BACKOFF_SECONDS` / `AUTHLETE_API_RETRY_ERROR_CODES` を調整。
3. Authlete IdP API にサービス単位で権限を確認できるエンドポイント（例: `/api/service/accessright/get`）が存在するか調査し、再試行ではなくレディネス判定での待機ができるか検討。
4. 並列化再開前に DuckDB のロック問題を解消し、検索系テストが並列実行で失敗しないよう対応。

## 未解決の疑問点

- Authlete はサービス単位のアクセス権一覧を取得できる API を提供しているか？ 存在する場合はそれを利用して権限適用完了を確認できる。
- 再試行の待機時間（例: 1〜2 秒で最大 3 回等）をどの程度に設定すべきか。CI 全体の所要時間への影響も考慮が必要。
- 並列化再開後、クリーンアップジョブが他ジョブのテスト中サービスを誤って削除しないよう調整が必要か？

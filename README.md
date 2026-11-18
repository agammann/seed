# Seed

Seed makes a smaller local JSON or CSV fixture for a failure you can check with a trusted test. It retains only selected fields, replaces selected values with consistent tokens, and tries removing records one at a time. It writes the resulting fixture and a review receipt. Seed requires Python 3.10 or newer and uses only the standard library.

## Try the synthetic example

```sh
python seed.py --trust-oracle examples/input.json examples/policy.json output -- python examples/oracle.py '{input}'
python -m unittest -v
```

Run from this directory and choose an unused output directory. In Windows Command Prompt, use `"{input}"`. The bundled example uses fictional values. You should see one retained row in `output/fixture.json` and a `REVIEW_REQUIRED` receipt in `output/receipt.json`. Inspect both files before sharing.

## Policy and oracle

Set each field in the policy's `fields` object to `keep` or `replace`. Seed drops fields absent from the list. Replacement assigns equal values the same synthetic token within a field. Optional `relationships` lists groups of replacement fields that use the same tokens. Check any foreign-key relationships, type requirements, inequality or format constraints your test depends on.

Use `--trust-oracle` only with a local test you trust. Seed runs it repeatedly without a shell and replaces one standalone `{input}` argument with a local temporary path. The test should return a distinct positive exit code for the intended failure and zero when the test passes. Seed checks the same original file bytes twice after detecting a failure. It compares the transformed fixture and each reduction trial against that baseline, then rechecks the exact output bytes. It uses only the exit code and discards the test's stdout and stderr. Similar exit codes, unrelated exceptions and intermittent failures can give false evidence.

`--timeout` bounds each invocation and `--budget` bounds the number of invocations. Seed leaves subprocess descendants and other side effects to your own isolation. Its temporary directory normally cleans up automatically. Interrupted runs or backups can retain copies of the original input.

## Inputs and review

Use UTF-8 JSON with a top-level list of flat objects, or UTF-8 CSV with a header of unique, nonempty field names. Choose an output location separate from the input and repository. Greedy removal works within the configured budget and can leave a fixture larger than the smallest possible result.

**Field replacement offers no anonymization guarantee.** Kept fields, token patterns, relationships and the failure itself can disclose private facts. The receipt includes input and output counts, the failure code, and a fixture hash. Review both files before sharing them.

## Positioning

[Picire](https://github.com/renatahodovan/picire) provides delta debugging; [Hypothesis](https://github.com/HypothesisWorks/hypothesis) provides property-based generation and shrinking; [Tonic Structural](https://www.tonic.ai/products/tonic-structural) provides data masking and relationship preservation. Seed combines a small local field policy and a single trusted failure oracle with a review receipt. It does not incorporate those projects or claim that this combination is unique. Its simple greedy reducer is deliberately not a replacement for Picire.

Original code is MIT licensed. No third-party code is included.

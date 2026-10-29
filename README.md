# Seed

Seed is an alpha, local-only CLI for making a smaller JSON or CSV fixture that still triggers a trusted failure test. It drops fields not explicitly listed, replaces selected values consistently, greedily removes records, and writes a receipt that requires human review. Python 3.10+; standard library only.

## Try the synthetic example

```sh
python seed.py --trust-oracle examples/input.json examples/policy.json output -- python examples/oracle.py '{input}'
python -m unittest -v
```

On Windows, use `"{input}"` instead of single quotes. Output must not already exist. Inspect `output/fixture.json` and `output/receipt.json` before sharing. The example contains fictional values only.

## Policy and oracle

`fields` is an allowlist: each field is `keep` or `replace`; omitted fields are removed. Replacement assigns deterministic synthetic tokens to equal values. Optional `relationships` groups replacement fields that share a token namespace, preserving equality across those fields. It does not validate foreign keys or preserve types, ordering, formats, inequality, or more complex constraints.

The oracle must be explicitly trusted: Seed executes it repeatedly without a shell, replacing one standalone `{input}` argument with a local temporary path. Write an oracle that returns a unique nonzero exit code **only** for the intended failure and zero otherwise. Seed compares the exit code twice on the original, after transformation, during reduction, and finally. It discards stdout and stderr. An ambiguous exit code, unrelated exception, or intermittent failure can give false evidence. Timeout and invocation count are bounded with `--timeout` and `--budget`, but subprocess descendants and side effects are not sandboxed. Use only tests you trust and isolate them yourself. Temporary files may contain the original input and are deleted on normal cleanup; interrupted runs or system backups may retain them.

**This is not anonymization.** Kept fields, token patterns, counts, relationships, metadata and the failure itself can disclose private facts. Review every output and receipt before sharing. No upload or safety certification is provided. The receipt contains record counts, failure code and a fixture hash, all potentially sensitive. Choose an output location separate from the input and repository. JSON must be a top-level list of flat objects; CSV is flat. Greedy record removal is budget-limited and does not promise a globally minimal result. This is an experimental prototype, not proof of market fit or safety.

## Positioning

[Picire](https://github.com/renatahodovan/picire) provides delta debugging; [Hypothesis](https://github.com/HypothesisWorks/hypothesis) provides property-based generation and shrinking; [Tonic Structural](https://www.tonic.ai/products/tonic-structural) provides data masking and relationship preservation. Seed combines a small local field policy and a single trusted failure oracle with a review receipt. It does not incorporate those projects or claim that this combination is unique. Its simple greedy reducer is deliberately not a replacement for Picire.

Original code is MIT licensed. No third-party code is included.

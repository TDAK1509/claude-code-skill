# Worked examples

## A docstring that says nothing, at length

Bad:

```python
def manifest_for_folder_at_ref(ref: str, folder: str, *, repo_root: Path | None = None) -> dict | None:
    """The compiled-input manifest ``folder`` declares at git ``ref``, or ``None`` when the folder
    holds neither file there. ``repo_root`` lets a caller point this at a different git checkout (a
    test's throwaway repo); it defaults to this module's own repo root."""
    root = repo_root if repo_root is not None else REPO_ROOT
    manifest_path, skill_md_path = _declaration_paths(folder)
    manifest_text = _show_at(root, ref, manifest_path)
    if manifest_text is not None:
        return _parse_yaml_mapping(manifest_text, source=f"{ref}:{manifest_path}")
    skill_md_text = _show_at(root, ref, skill_md_path)
    if skill_md_text is None:
        return None
    return _frontmatter_manifest_at_ref(
        root=root, ref=ref, folder=folder, skill_md_text=skill_md_text, skill_md_path=skill_md_path
    )
```

Good:

```python
def detect_skill_manifest(ref: str, folder: str, *, repo_root: Path | None = None) -> dict | None:
    """If skills folder has both manifest.yaml and SKILL.md, use manifest.yaml, otherwise use SKILL.md."""
    root = repo_root if repo_root is not None else REPO_ROOT
    manifest_path, skill_md_path = _declaration_paths(folder)
    manifest_text = _show_at(root, ref, manifest_path)
    if manifest_text is not None:
        return _parse_yaml_mapping(manifest_text, source=f"{ref}:{manifest_path}")
    skill_md_text = _show_at(root, ref, skill_md_path)
    if skill_md_text is None:
        return None
    return _frontmatter_manifest_at_ref(
        root=root, ref=ref, folder=folder, skill_md_text=skill_md_text, skill_md_path=skill_md_path
    )
```

Two things changed. The body did not.

### The name

`manifest_for_folder_at_ref` is a noun phrase. It names the return value and the
two arguments, which the signature already shows. It does not say what the
function does.

`detect_skill_manifest` says it. The function picks one of two declaration files.
"Detect" is the work. See the `function-names-are-verbs` skill.

The dropped words are not lost. `ref` and `folder` are in the signature. A name
does not repeat its own parameters.

### The docstring

The bad docstring is three lines and fifty words, and a reader still does not
know the rule. It describes the return type, restates the arguments, and
explains a test's use of `repo_root`. All of that is in the signature.

The good docstring is the rule itself, in one sentence: which file wins when both
exist. That is the one thing the code makes the reader work for.

`repo_root` needs no prose. The name says what it is and the default says where
it points. A parameter that needs a paragraph is a design problem, not a
documentation problem.

## The test to copy

Delete the docstring and read the function. Write down the one thing you still
had to work out. That sentence is the docstring. Everything else was the
signature in words.

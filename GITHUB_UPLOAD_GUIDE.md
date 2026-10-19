# Upload this replacement case study separately

This package is **Lab Reagent Inventory & FEFO Allocation**. It is independent of the Laboratory Specimen Tracker, which stays as your other case study. No GitHub repository has been created or published automatically.

Suggested repository name:

```text
lab-reagent-inventory-fefo-c
```

Suggested description:

> C11 lab-reagent inventory simulation with batch-wise expiry tracking, deterministic FEFO allocation, confirmation/rollback and automated tests.

## Steps

1. Download `Biomedical-Lab-Reagent-Inventory-FEFO.zip` and use Windows **Extract All**. No C compiler is required just to extract/upload it.
2. Create a new GitHub repository using the suggested name (or another name you prefer).
3. Choose Public only if you want the coursework public. If Private, invite your teacher as a collaborator; the link alone does not grant access.
4. Leave automatic README/ignore/license creation unchecked for this empty repository; the package already provides a README and `.gitignore`. Choose a license yourself if you want one.
5. Select **uploading an existing file** or **Add file -> Upload files**.
6. Open the extracted folder and upload its **contents**, so `main.c` and `README.md` are at the repository root. Keep the `examples/`, `tests/` and optional `.github/` subfolders. Do not upload only the ZIP.
7. Commit the files, check README/documentation links and copy this repository's actual URL.
8. Keep/upload the Laboratory Specimen Tracker in its own separate repository and copy that URL too. Send your teacher those two actual repository links.

GitHub's ordinary file upload does not unpack a ZIP. Its repository page displays source/documents rather than running the interactive C app. The optional Actions workflow can compile/test the program after publication; check the actual remote run rather than assuming a local pass means a remote pass.

## Keep generated/private files out

Do not upload executables, objects, runtime `reagent_batches.txt`, `.tmp`/`.bak` files, caches, secrets or real laboratory data. Fictitious examples in `examples/` are meant to be included. `.gitignore` helps with Git commands; it does not automatically filter files selected through a browser upload.

If a browser omits dot-files/folders, use GitHub's **Create new file** with `.gitignore` or `.github/workflows/c-tests.yml` and copy the supplied contents. The C program does not require the optional workflow.

Acknowledge assistance according to your college's rules. Learn the algorithm and main functions before presenting; do not claim a production medical system or completely original unaided work if that is not accurate.

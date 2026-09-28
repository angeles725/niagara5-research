# Preserved external sources — <SUBJECT>

> Registry of every document/page downloaded during the research. Research-SDD rule:
> URLs die; evidence does not. Blocks cite the **local file**,
> not the URL. This registry is maintained by `research-sdd/toolbelt/fetch-doc.sh` (automatic append).

| File | Type | Origin (URL) | Date (UTC) | sha256 | Blocks that cite it |
|---|---|---|---|---|---|
| datasheets/example.pdf | datasheet | https://... | 2026-06-28T00:00:00Z | abc123… | [Block K] |
| /mnt/c/PowerB/PowerB-4.15.3.28/bin/ext/nre.jar | N4-4.15 jar | local OEM install (PowerB 4.15.3.28) | 2026-09-28T00:00:00Z | 4340f0f6777f6886aba8d6d07eb83e84d02dba7bac980374fe82c792f2670d1f | [Block 84] |
| /mnt/c/PowerB/PowerB-4.15.3.28/modules/baja.jar | N4-4.15 jar | local OEM install | 2026-09-28T00:00:00Z | a58f5ce91d92fa3c35117bb7fd76445ee1afdf4cb5209c80525347c0aee95263 | [Block 84] |
| /mnt/c/PowerB/PowerB-4.15.3.28/modules/bacnet-rt.jar | N4-4.15 jar | local OEM install | 2026-09-28T00:00:00Z | ad2f370a7a272974a34af7e5e53ee83aa6486d96f4cf20fba8ceb68af3ff3131 | [Block 84] |
| /mnt/c/PowerB/PowerB-4.15.3.28/modules/tagdictionary-rt.jar | N4-4.15 jar | local OEM install | 2026-09-28T00:00:00Z | 26165db435e0c7a9db1f1e4fb274321f9b2ea9cdc4e2bb54d26a73c979280fda | [Block 84] |
| /mnt/c/PowerB/PowerB-4.15.3.28/modules/alarm-rt.jar | N4-4.15 jar | local OEM install | 2026-09-28T00:00:00Z | c2df15ae75c5a3557ce721ef0554b5794650b227d9e8fb3112793f03760f6bd7 | [Block 84] |
| /mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar | N5 jar | local N5 beta install | 2026-09-28T00:00:00Z | d563a334e02ef739d53bb67ddf48de96582b787dff89a8ab1c5140cdf381f9f7 | [Block 84] |
| N5 bin/nre.dll | N5 native | local N5 beta install | 2026-09-28T00:00:00Z | a6317e8b024ed823ebe857113bff4378600fc2bd41890309696375dce91239c4 | [Block 63], [Block 87] |
| N5 bin/njre.dll | N5 native | local N5 beta install | 2026-09-28T00:00:00Z | 1b8b0074c79dc148e479602bb5bb1a2245f3549db421ccb6534bca7f6a4dfd0b | [Block 76], [Block 87] |
| N5 bin/n5mig.exe | N5 native | local N5 beta install | 2026-09-28T00:00:00Z | 95b5deae0afc4a0b68361f82d4696398691e4b2130a285dce471ab3aa5c97e46 | [Block 87] |
| N5 bin/niagarad.exe | N5 native | local N5 beta install | 2026-09-28T00:00:00Z | 64fd6403fe00bc1b8b940254682bad454806e1983f3fe54343c56c035c24944b | [Block 76], [Block 87] |
| manuals/docNcs.pdf | manuals | https://downloads.onesight.solutions/Tridium/Niagara%204%20Documents/docNcs.pdf | 2026-09-28T01:08:19Z | c1eccc7e5f6d5dade2efc08699719f22122dc914afd909a614d1a09951d6b4cf | [Block 88] |

## Structure

```
sources/
  datasheets/      ← manufacturer datasheets
  manuals/         ← official manuals / guides
  web-snapshots/   ← pages and forums converted to markdown (pandoc)
  extracted/       ← extracted text (extract-pdf.sh: pymupdf4llm text-layer → ocrmypdf/tesseract OCR fallback)
```

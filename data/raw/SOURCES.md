# Data sources

Every download or data pull: link, date, what it is, license or terms. Raw files are never edited by hand.

## 1. Facade filings, summary counts only (Oct 16, 2026)
- What: "DOB NOW: Safety – Facades Compliance Filings," NYC Open Data, dataset `xubg-57si`
  (https://data.cityofnewyork.us/d/xubg-57si). 87,383 rows, 40 columns (row count from the API metadata, Oct 16, 2026).
- How: aggregate queries through the Socrata API (counts by cycle, filing type, status, and by month of
  `filing_date` and `field_inspection_completed_date` for each block-digit group). No rows were saved; results were
  read on screen and summarized in `PLAN.md`. Script: `src/spike_bunching_2026-10-16.py`.
- License or terms: the dataset page lists none (`license: None` in the API metadata). The nyc.gov Open Data page
  links a general terms of use (https://www.nyc.gov/main/terms-of-use), not yet read. **Check before the first full
  download.** (Done Oct 17, 2026: see section 2.)
- Note: the full file includes owner and inspector names and addresses. They must be dropped in processing and never
  used or published.

## 2. Terms check for NYC Open Data reuse (read Oct 17, 2026, by Claude)
**Finding: reuse is allowed. Downloading the full file and publishing derived charts and write-ups is covered, with
one condition: say where the data came from, which version, and what we changed.** No account, key or payment is
needed. Two things could not be checked; they are listed at the end.

- **The law that governs it:** NYC Administrative Code section 23-502(d), added by Local Law 11 of 2012 (the City's
  Open Data Law, unrelated to the facade program's "Local Law 11") and amended by Local Law 251 of 2017.
  - Local Law 11 of 2012, passed Feb 29, 2012, approved Mar 7, 2012: https://intro.nyc/local-laws/2012-11
  - Local Law 251 of 2017, passed Nov 16, 2017, effective immediately: https://intro.nyc/local-laws/2017-251
  - Paraphrase of the current subdivision (d): public datasets must be offered with no restrictions on their use. The
    Department of Information Technology and Telecommunications may require anyone republishing a dataset, or an app
    built on it, to identify its source and version and describe any changes. Measures that keep the portal working
    or protect it from abuse do not count as restrictions. The only quote: "without any restrictions on their use".
  - Section 23-504: the data is provided for information only, with no warranty of accuracy or fitness. So the
    write-up must not present any figure as an official DOB statistic.
- **nyc.gov Terms of Use** (https://www.nyc.gov/main/terms-of-use, read in the browser pane Oct 17, 2026): covers the
  nyc.gov website. It does not mention Open Data, datasets, APIs or automated access. Its only relevant rule is not to
  "disrupt" the site or its servers, so downloads must be gentle (few requests, pages of at most 50,000 rows). It
  names no Open Data terms link.
- **Dataset page** (https://data.cityofnewyork.us/d/xubg-57si, read Oct 17, 2026): lists no license and no
  dataset-specific terms. Provider: Department of Buildings. The page shows an Export button and about 34,000
  downloads. The API metadata also says `license: None` (pulled Oct 17, 2026).
- **API access:** Socrata (the portal software) says an app token is optional. Unauthenticated requests are allowed
  but throttled harder per IP address (https://dev.socrata.com/docs/app-tokens.html, read Oct 17, 2026). No account,
  key or payment is needed for this download.
- **What the write-up must carry:** the dataset name and ID, the date pulled, the dataset's last-update time, and a
  line saying what was filtered or aggregated. A line such as "Data: NYC Department of Buildings via NYC Open Data
  (xubg-57si), pulled <date>; aggregated and charted by us" does it.
- **UNVERIFIED, two gaps:**
  1. I could not open the live code library (American Legal returned HTTP 403 and Firecrawl was out of credits), so I
     have not confirmed that no amendment after Local Law 251 of 2017 changed subdivision (d). A public mirror
     (https://nyc-laws.readthedocs.io/en/latest/nycadmincode/t23/c05/) still shows the 2012 wording and no date.
  2. The old Open Data portal terms page (https://www.nyc.gov/html/data/terms.html) now returns HTTP 404. I only saw
     a search-engine description of it (second-hand), which said portal users also accept nyc.gov's terms and any
     extra terms set by the data-providing agency. This dataset's page shows no such extra terms.
  For certainty, the Open Data Team's contact page is https://www.nyc.gov/opendata/contact-us. Whether to email them
  was left to Jayden Ling and has not been done.

## 3. Full download of the facade filings file (Oct 17, 2026)
- What: "DOB NOW: Safety – Facades Compliance Filings," NYC Open Data, dataset `xubg-57si`
  (https://data.cityofnewyork.us/d/xubg-57si). Provider: Department of Buildings. Updated every weekday.
- How: free Socrata API, no key, no token, no account (`https://data.cityofnewyork.us/resource/xubg-57si.json`,
  50,000 rows per request, ordered by the portal's row id, 2-second pause between requests). Script:
  `src/download_xubg_57si.py`. Pulled Oct 17, 2026 at 21:13 UTC. The dataset itself was last updated Oct 17, 2026 at
  17:32 UTC (portal metadata field `rowsUpdatedAt`).
- Rows: **87,455**, 40 columns. The row count was the same before and after the download and the update time did not
  change, so this is one consistent snapshot. (The Oct 16 summary query counted 87,383, so about 72 rows were added
  in a day.)
- Files in `data/raw/` (gitignored, never edited):
  - `xubg-57si_2026-10-17_page00.json` (50,000 rows, 44.1 MB), `xubg-57si_2026-10-17_page01.json` (37,455 rows, 35.7 MB)
  - `xubg-57si_2026-10-17_meta.json`: counts, update time, column list, page list
  - `docs_xubg-57si/DOB_NOW_Safety_Facades_Compliance_Filings_Data_Dictionary_2025_12_12.xlsx`: the official data
    dictionary from the dataset page (97 KB, same terms as the dataset). It is thin: it lists example values but does
    not say how `filing_status` differs from `current_status`.
  - SHA-256 (to prove the files were not edited): page00 `238bea2194f615e48a16953def084d4cac1162e80ce84290cab7b29c386c12e9`;
    page01 `0165da4d7cf4476b52781f83e5083a626f8f068c6620cc22b86789be094cf0b4`.
- License or terms: see section 2. Reuse allowed; the write-up must name the dataset, the pull date and what we changed.
- Columns (40): `tr6_no`, `control_no`, `filing_type`, `cycle`, `bin`, `house_no`, `street_name`, `borough`, `block`,
  `lot`, `sequence_no`, `submitted_on`, `current_status`, `qewi_name`, `qewi_bus_name`, `qewi_bus_street_name`,
  `qewi_city`, `qewi_state`, `qewi_zip`, `qewi_nys_lic_no`, `owner_name`, `owner_bus_name`, `owner_bus_street_name`,
  `owner_city`, `owner_zip`, `owner_state`, `filing_date`, `filing_status`, `prior_cycle_filing_date`, `prior_status`,
  `field_inspection_completed_date`, `qewi_signed_date`, `late_filing_amt`, `failure_to_file_amt`,
  `failure_to_correct_amt`, `exterior_wall_type_s_`, `exterior_wall_material_s_`, `comments`,
  `exterior_wall_type_other_description`, `exterior_wall_material_other_description`. There is no height or
  stories column.
- **Personal data in the raw file:** inspector (QEWI) names, business names, addresses and license numbers; owner
  names, business names and addresses; street addresses; and a free-text `comments` column that can contain names,
  phone numbers and emails. All are dropped in the first processing step (`src/process_facades.py`) and never used,
  printed, charted or published.

## 4. PLUTO tax-lot file (pulled Oct 18, 2026, 04:37 UTC)
- What: Primary Land Use Tax Lot Output (PLUTO), NYC Open Data `64uk-42ks` (https://data.cityofnewyork.us/d/64uk-42ks). Provider: Department of City Planning (DCP). Release **26v2** (August 2026), per the dataset description and the DCP page (https://www.nyc.gov/content/planning/pages/resources/datasets/mappluto-pluto-change, read Oct 17, 2026). This is a **current snapshot**, not a 2015 to 2024 history: lot traits (owner type, floors) are as of Aug 2026.
- Columns: Only borough, block, lot, bbl, ownertype, numfloors were requested (`$select`). The owner name column (`ownername`), addresses and everything else were never downloaded. Only the owner CATEGORY is ever used.
- How: free Socrata API, no key, token or account (`https://data.cityofnewyork.us/resource/64uk-42ks.json`, 50,000 rows per request, ordered by the portal's row id, 2-second pause). Script: `src/download_open_data.py`. The dataset was last updated Aug 24, 2026 at 20:48 UTC (`rowsUpdatedAt`); it did not change during the download.
- Rows: **858,284** (whole dataset; the count was the same before and after, so one consistent snapshot). Files: 18 pages named `64uk-42ks_2026-10-18_pageNN.json` in `data/raw/` (gitignored, never edited), 81,989,193 bytes in total, plus `64uk-42ks_2026-10-18_meta.json`.
- Terms: the Open Data metadata lists no license; attribution "Department of City Planning (DCP)". The DCP page carries only a disclaimer (data "for informational purposes only", no warranty, City not liable); it says nothing about fees, accounts, keys or attribution, and does not restrict reuse. Reuse is allowed under section 2 (NYC Open Data Law). Cite release 26v2 and the pull date; do not present PLUTO as warranted. Checked Oct 17, 2026 by a helper from metadata and DCP pages only.
- SHA-256 of each page file is in the meta file (`pages[].sha256`); the first and last are: page00 `59766bc3ae2a051cc4db854466115cfa7c69c5f6536cca884452445d5e88d86b`; page17 `9fd72da5915d27b4d64e886aee8daa96d65aaf4c1a5b60265567fa23328e035f`.
- Nothing was read or printed from the rows: only file names, sizes, the row count and the names of the keys (to confirm only the requested columns arrived).

## 5. DOB NOW approved permits (pulled Oct 18, 2026, 04:43 UTC)
- What: "DOB NOW: Build – Approved Permits," NYC Open Data `rbx6-tga4` (https://data.cityofnewyork.us/d/rbx6-tga4). Provider: Department of Buildings (DOB). Updated daily.
- Columns: Requested with `$select`: bin, block, lot, work_type, permit_status, filing_reason, work_permit, sequence_number, approved_date, issued_date, expired_date. The whole dataset was taken with no filter on work type. Applicant, permittee, owner and filing-representative names and addresses, job descriptions and cost columns were never downloaded.
- How: free Socrata API, no key, token or account (`https://data.cityofnewyork.us/resource/rbx6-tga4.json`, 50,000 rows per request, ordered by the portal's row id, 2-second pause). Script: `src/download_open_data.py`. The dataset was last updated Oct 17, 2026 at 18:41 UTC (`rowsUpdatedAt`); it did not change during the download.
- Rows: **1,016,520** (whole dataset; the count was the same before and after, so one consistent snapshot). Files: 21 pages named `rbx6-tga4_2026-10-18_pageNN.json` in `data/raw/` (gitignored, never edited), 324,735,974 bytes in total, plus `rbx6-tga4_2026-10-18_meta.json`.
- Terms: metadata license None; attribution "Department of Buildings (DOB)"; no dataset-specific terms or disclaimers; no account, key or payment needed. Reuse allowed under section 2.
- SHA-256 of each page file is in the meta file (`pages[].sha256`); the first and last are: page00 `df556b3fc997d1aef4ac829ab6e38c58c68ef8e054c0ae5d698d2c0ecfb6d78d`; page20 `27a7efb1a397ffa6c7121fe350c024162766e3efbc868eb040906795e4895cf1`.
- Nothing was read or printed from the rows: only file names, sizes, the row count and the names of the keys (to confirm only the requested columns arrived).

## 6. DOB permit issuance (older BIS system) (pulled Oct 18, 2026, 04:53 UTC)
- What: "DOB Permit Issuance," NYC Open Data `ipu4-2q9a` (https://data.cityofnewyork.us/d/ipu4-2q9a). Provider: Department of Buildings (DOB). Updated daily. Covers permits issued in the older BIS system only (current permits are in DOB NOW).
- Columns: Requested with `$select`: bin__, permit_type, permit_subtype, permit_status, filing_date, issuance_date, expiration_date. The whole dataset was taken with no filter on permit type. Permittee, owner, site-safety-manager and superintendent names, phone numbers and addresses were never downloaded. The dates are text in this dataset.
- How: free Socrata API, no key, token or account (`https://data.cityofnewyork.us/resource/ipu4-2q9a.json`, 50,000 rows per request, ordered by the portal's row id, 2-second pause). Script: `src/download_open_data.py`. The dataset was last updated Oct 17, 2026 at 23:24 UTC (`rowsUpdatedAt`); it did not change during the download.
- Rows: **3,990,985** (whole dataset; the count was the same before and after, so one consistent snapshot). Files: 80 pages named `ipu4-2q9a_2026-10-18_pageNN.json` in `data/raw/` (gitignored, never edited), 658,543,732 bytes in total, plus `ipu4-2q9a_2026-10-18_meta.json`.
- Terms: metadata license None; attribution "Department of Buildings (DOB)"; no dataset-specific terms; no account, key or payment needed. Reuse allowed under section 2.
- SHA-256 of each page file is in the meta file (`pages[].sha256`); the first and last are: page00 `7fc9688559d598155ced8d07e20e8bb0e24dc8cece198ace2f3b34e12948f091`; page79 `46c4c670d9ba51e54673dc5164dbf86024bded9f22c99f3e7816a52bd0f73ed5`.
- Nothing was read or printed from the rows: only file names, sizes, the row count and the names of the keys (to confirm only the requested columns arrived).

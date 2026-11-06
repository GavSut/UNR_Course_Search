# Course Search Studio — UNR

A standalone Python GUI and a complete static website for building custom MyNEVADA console scripts and planning schedules from the exported results. Made for students across majors and course levels. CSV is the default result download; JSON and TSV are also available.

**Supported system:** the observed UNR MyNEVADA / PeopleSoft Class Search interface. This is an independent student tool, not an official university service. “Any student” means any UNR student; other universities need their own tested page adapter.

## Use the Python app

Requires Python 3 with Tkinter. There are no third-party Python dependencies.

```bash
python3 UNR_Course_Script_Builder.py
```

On Windows, `py UNR_Course_Script_Builder.py` also works when the Python launcher is installed. If Python reports that Tkinter is missing, use a Tk-enabled Python installation. Test Tk separately with `python3 -m tkinter`.

1. Choose subjects in the **Subjects** tab, or enter additional subject codes.
2. By default the script uses the term already selected in MyNEVADA. To choose a term explicitly, turn that checkbox off and enter the year/season or exact term label.
3. Set any course-number, title, instructor, class-status, component, day, and time filters. Blank fields impose no restriction. The initial course range is unrestricted.
4. Choose CSV, JSON, or TSV in **Export**. Copy the script or save it as `.txt`.
5. Sign in to MyNEVADA, open Class Search, and paste the whole script into the developer console with the execution context set to **top**. Keep the tab open while it runs.

For Firefox: Command–Option–K on Mac; Ctrl–Shift–K on Windows/Linux. The script performs ordinary class searches; it does not select or enroll in classes.

Saved settings are interchangeable between the web and Python versions. Settings from the previous builder can also be imported; their existing filters are preserved, with the new default of using the selected MyNEVADA term. Review the term checkbox after loading older settings.

The Python command-line generator is also available:

```bash
python3 UNR_Course_Script_Builder.py --generate my_settings.json --output my_search.txt
```

## Publish the website on GitHub Pages

The `docs/` folder is the complete, built website. It includes the Python download. No Node server, database, API key, external fonts, installation, or build step is required to host the supplied files.

1. Unzip this project and create a GitHub repository, such as `unr-course-search`.
2. Upload the **contents** of the project folder to the repository root. Preserve the `docs/assets/` and `docs/downloads/` subfolders. Do not upload only the ZIP file or add another enclosing folder.
3. In the repository, open **Settings → Pages**.
4. Under **Build and deployment**, choose **Deploy from a branch**.
5. Select **main**, choose **/docs**, then save.
6. Wait for GitHub's deployment to finish. Open the URL GitHub displays on that Pages screen.

All site asset and download links are relative, so it works on a GitHub project subpath. `.nojekyll` is included. A public repository is the simplest route; private-repository Pages availability depends on the GitHub plan.

Publishing instructions: [GitHub's official Pages source guide](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

This package contains deployable source. It does not create a repository or publish a URL automatically.

## Schedule builder (new page)

Open **Schedule builder** in the navigation, or `docs/schedule.html`. It works with the existing GitHub Pages `/docs` setup; no backend or extra dependency is needed.

- Upload or drag in one or more results files: the original `UNR-course-export-v5` JSON, the current builder's JSON with raw `courses`, or its CSV/TSV. A section's multiple meetings stay together. Repeat imports deduplicate section IDs; a newer imported section replaces that section's earlier snapshot. Imports from different terms get separate plans.
- Filter by course/title/class number, subject, level, instructor, status, component, allowed days and time window. Star courses, hide research sections, or hide overlaps with the current plan. TBA is never inferred to mean asynchronous.
- Add and remove sections; adding an alternative for the same course and component replaces the prior component. Labs/discussions are selected separately. The tool cannot infer registration pairings from these exports.
- Use week, day, or agenda calendars, actual meeting date ranges, weekend support, and overlap layout. Date-aware conflict checks span the full term, including personal recurring blocks and optional 10/15/30-minute buffers.
- Enter credits once per course, not once per lecture/lab. Totals include a numeric 700–799 subtotal and explicitly show missing credit values. This is not a degree audit.
- Create, rename, duplicate, delete, and compare plans. Add course notes and confirm that component rules were checked in MyNEVADA.
- Star up to eight courses and choose **Explore starred-course combinations** for up to twelve time-compatible proposals. This bounded search considers one section of every component type present, dated/timed sections only, personal blocks, and the time buffer. It does **not** verify allowed component pairings or use the explorer filters/current course selections as constraints. Each proposal can become a separate plan for review. Search limits are shown rather than implying exhaustive coverage.
- Export recurring events as `.ics` in `America/Los_Angeles`, including DST transitions; export plan CSV or print/save PDF. Undated or untimed meetings are omitted from ICS with a warning. Optional fallback term dates can fill missing dates; no holiday exclusions are inferred.
- Results and plans autosave in browser local storage. Save a full JSON backup to restore on another browser. Restore replaces browser-local data only after confirmation. Storage failures show a backup warning. Files are processed locally; none are uploaded to a server.

**Upgrade an existing GitHub Pages deployment:** replace its `docs/` folder with the updated `docs/` folder in this package. Keep your repository's existing Pages settings. If maintaining source, replace the project files as well. No personal course exports are bundled; the built-in sample uses explicitly fictional courses.

## Preview locally

From the project root:

```bash
python3 -m http.server 8000 --directory docs
```

Open `http://localhost:8000`. The static site can also be opened from `docs/index.html`, though clipboard restrictions vary for local files; Download script still works. The website generates a script locally. It cannot search a signed-in MyNEVADA account directly from a different website.

## Result files

CSV and TSV start with a **Search summary** row followed by one row per meeting. A section with multiple distinct meeting blocks can occupy several rows. Filter `Record type` to `Section` if you want only class rows.

| Columns | Meaning |
| --- | --- |
| Match | `Matches selected filters` or `Needs review` |
| Subject, Course number, Course title | Course identity |
| Class number, Section, Component | Registration section identity and type |
| Class status | The status displayed during collection |
| Days, Start time, End time | Parsed meeting schedule; times use 24-hour campus-local time |
| Meeting time as listed | Original displayed text, including TBA or unusual schedules |
| Room, Instructor | Displayed meeting details |
| First meeting date, Last meeting date | ISO dates where recognizable |
| Schedule verified | Whether all listed schedules were parsed successfully |
| Notes | Match/review explanations and course notes |
| Term, Search completeness, Search notes, Collected at | Provenance, completion, errors, and timestamp |

The table contains matched sections and, by default, sections needing review. Turn off **Include needs-review sections** to omit the latter from CSV/TSV. The summary still reports their count. Excluded sections are available in JSON.

A zero-result file still has headers and a summary. An incomplete search has `PARTIAL` in the filename and a clear completeness label in each row. Search notes identify unfinished subjects. Unrecognized rows are flagged; download JSON to inspect their raw content.

JSON always retains `courses`, `searches`, `filters`, `summary`, and `results`, including `matched`, `needsReview`, `excluded`, and `unparsedRows`. It is the most complete audit format.

Run any of these commands in the **same MyNEVADA browser tab** after the script starts:

```javascript
UNRexport.stop()         // stop; the script saves partial results
UNRexport.download()     // download the selected format again
UNRexport.downloadCSV()  // readable spreadsheet
UNRexport.downloadJSON() // full audit, including raw data
UNRexport.downloadTSV()  // tab-separated spreadsheet
```

## Matching rules and limits

- Every listed meeting of a section must fall entirely within the selected hours and use only checked days. Start/end boundaries are inclusive.
- TBA, missing, overnight, and unrecognized schedules are not called time matches. If time filtering is on, otherwise eligible sections are retained for review. If time filtering is off, they can match the other criteria, with `Schedule verified = No`.
- Title keywords use case-insensitive ANY-match. Instructor is a case-insensitive substring. Numeric ranges do not establish degree or credit eligibility.
- Matches are individual sections, not enrollment-ready lecture/lab bundles. Verify required components, credits, prerequisites, permissions, and seats in MyNEVADA.
- No delivery-mode or credit filter is presented because the collected result rows do not reliably expose those fields. TBA does not prove asynchronous or online delivery.
- The script collects closed classes as well, then applies status and most other filters locally. Minimum course number is also sent to the search form; maximum is applied to the collected results.
- Broad subjects can hit MyNEVADA result limits or timeout. Narrow the subject/minimum-number search and inspect the partial file. End-of-pages is based on recognized controls, not an independent university database count.
- A missing term, unfamiliar page layout, pagination loop, or unavailable control stops the run with the data collected so far. Layout changes may require updating the adapter.

## Privacy and security

The website uses only its own static files, with no analytics, backend, tracking code, or external scripts. The Python generator has no network dependencies. Neither asks for passwords or sends search results to a server. The schedule page reads selected results locally and stores plans in the browser; it does not share them between students. Settings are downloaded only when the user chooses Save settings. GitHub still serves the page under its normal hosting policies.

The generated script runs in the student's own signed-in browser session, reads displayed course results, and uses normal search controls. It automatically acknowledges only recognized class-search messages, never enrollment prompts. It restricts itself to UNR domains. User-entered filters are JSON-encoded rather than evaluated as JavaScript. CSV/TSV quote every field and neutralize common spreadsheet formula prefixes.

Do not commit personal result exports or saved settings to a public repository. The included `.gitignore` excludes the tool's usual export names.

## Maintain or customize

| File | Purpose |
| --- | --- |
| `src/browser-template.js` | UNR-specific page controls, collection, pagination, downloads |
| `src/matching.js` | Section grouping and conservative matching |
| `src/exports.js` | Readable CSV/TSV table and serialization |
| `src/core.js` | Web configuration validation and generator |
| `src/desktop.py` | Tkinter GUI source with build placeholders |
| `data/subjects.json` | Searchable starter subject suggestions |
| `data/instructions.txt` | Shared user instructions |
| `scripts/build.py` | Embeds the shared engine in web and Python outputs |
| `docs/` | GitHub Pages publishing folder |
| `docs/schedule.html`, `docs/assets/schedule.js`, `docs/assets/schedule.css` | Schedule builder page and UI |
| `src/schedule-engine.js` | Import, conflict, calendar export, credit, backup, and suggestion logic |
| `tests/` | Synthetic matching/export tests and Python/web parity tests |

After source changes, rebuild and commit the generated outputs too:

```bash
python3 scripts/build.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/test_engine.js tests/test_schedule.js
```

Tests require Python 3 and Node.js with the built-in test runner. Running the desktop GUI does not require Node. Synthetic test cases contain no student account information.

The starter subject list is intentionally non-exhaustive. Additional codes are accepted directly. Its code suggestions were checked against the [UNR liberal arts prefix list](https://www.unr.edu/liberal-arts/academic-advising/degree-framework/breadth-requirement), [NSHE taxonomy](https://ir.nevada.edu/cip_cluster_and_weights.php), and the earlier successful UNR export. Subject existence does not establish a section offering in a particular term.

## Validation for this release

- Nine JavaScript tests and five Python tests pass, including multiline meetings, continuation rows, duplicates, TBA, numeric/status filters, JSON-safe generation, CSV quoting, partial/empty results, and web/Python settings parity.
- The matching engine was also checked against the supplied 524-section export: all sections were retained, with no unparsed result rows. With all-day time verification on, 91 sections had recognized schedules and 433 needed review.
- Browser checks covered the website's initial state, missing-subject validation, subject search/selection, range presets, weekday controls, format choice, script generation, and copy confirmation.
- The new exporter has not been run against a live signed-in MyNEVADA session. The desktop window has not been visually tested in this headless environment. These limits do not affect the recorded automated checks.

## Schedule-builder validation

- 28 JavaScript tests (9 existing + 19 scheduling) and 5 Python tests pass, covering imports, multi-meeting sections, date-aware conflicts, buffers, TBA, component credit counting, backup validation, CSV formula escaping, timezone-aware ICS, and bounded combinations.
- The supplied broad export was imported successfully: 1,477 sections across 316 courses, zero unparsed rows. Its incomplete EPSY search remains visible as a partial-coverage warning. User results are test inputs only and are not shipped.
- Browser QA covered page navigation, sample data, real JSON upload, course filtering, overlapping calendar blocks, generated combinations saved as a new plan, manual credit entry, personal-block conflicts, plan comparison, day/agenda views, and persistence through reload.
- Registration restrictions, prerequisites, seats, credit values, and valid lecture/lab pairings still require MyNEVADA review.

- Calendar generation passes recurrence, timezone, and omitted-meeting tests. The browser download event did not return a saved-file path in this environment, so saving the calendar to disk was not independently confirmed. A persistent download link is shown if automatic download is blocked.

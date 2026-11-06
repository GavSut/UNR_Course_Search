# Course Search Studio — UNR

**Find classes. Compare your options. Build a semester that fits.**

Course Search Studio helps University of Nevada, Reno students turn MyNEVADA course-search results into a practical schedule. Explore classes across departments, keep track of favorites, and compare possible schedules on a calendar before registering.

It is an independent student tool for UNR's MyNEVADA Class Search, not an official university service. Course registration takes place in MyNEVADA.

## What you can do

| Explore your options | Plan your semester |
| --- | --- |
| Search across multiple subjects and course levels | View classes in week, day, or agenda layouts |
| Filter by course, instructor, availability, days, and times | Spot overlaps and leave a buffer between meetings |
| Star courses you want to consider | Explore time-compatible combinations of starred courses |
| Upload and combine exported course results | Save, duplicate, and compare alternative plans |
| Review original meeting details and search coverage | Track entered credits, including a 700-level subtotal |
| Keep course notes and review required components | Add work, research, or other recurring commitments |

## Get started

### 1. Choose what to search

Open **Search builder** on the website. Select subjects and any course-number, title, instructor, availability, or scheduling preferences. By default, the script uses the term you have selected in MyNEVADA.

Generate your search script, then copy it or download it as a text file. You can save your settings to reuse later.

### 2. Collect your MyNEVADA results

Sign in to MyNEVADA and open **Class Search**. Confirm the term, open your browser's developer console, select the **top** execution context, and paste the complete generated script. Leave the tab open while it searches and downloads your results.

For Firefox, open the console with **Command–Option–K** on Mac or **Ctrl–Shift–K** on Windows/Linux. The script uses the usual class-search controls and does not enroll you in classes.

Choose CSV for spreadsheet-friendly results, JSON for the most complete record, or TSV for tab-separated data. If you already have a compatible results file, go directly to the next step.

### 3. Build your schedule

Open **Schedule builder**, choose **Upload results**, or drag your files onto the page. It accepts this tool's JSON, CSV, and TSV exports, including earlier UNR course-export JSON files. You can import several files; repeated sections are merged, and different terms have separate plans.

Filter the course list, star promising courses, and add sections to your plan. Use the calendar to see your week, review conflicts, and add recurring personal commitments. The sample data let you explore the builder before importing your own results.

### 4. Compare, save, and take it with you

Create multiple plans to compare alternatives. **Explore starred-course combinations** suggests schedules using your favorites, personal commitments, and selected time buffer. Review each proposal's section choices before using it.

Plans save automatically in the current browser. Use **Save backup** to keep a portable copy or move your work to another browser. You can also export a calendar file (`.ics`), download a plan as CSV, or print a schedule and save it as PDF.

## A few things to check before registering

- **Credits:** enter missing credit values once per course. Lectures and labs are not automatically counted as separate courses. The 700-level subtotal is a planning aid; it does not determine which credits your program will accept.
- **Required components:** review lecture, lab, and discussion requirements in MyNEVADA. Suggested combinations check meeting times, but cannot confirm which sections may be registered together.
- **TBA and missing information:** an unknown time does not mean a class is online or asynchronous. Missing or unrecognized meetings are flagged for review; they cannot be fully checked for conflicts.
- **Availability and coverage:** results are a snapshot from when you ran the search. Partial searches identify unfinished subjects. Confirm current seats, prerequisites, permissions, and meeting details before registering.
- **Calendar exports:** check term dates and university breaks. Meetings without usable dates or times are omitted with an explanation; holidays are not removed automatically.

## Your files and privacy

Uploaded course results are processed in your browser and are not sent to a server. Plans are stored in that browser and are not shared with other students. The site has no analytics or tracking scripts and never asks for your MyNEVADA password.

Clearing browser data can remove saved plans, so keep a backup of work you want to retain. Only import a backup when you intend to replace the plans and results currently saved in that browser.

## Prefer a desktop search builder?

A Python version is available through the website. It creates the same search scripts, and saved search settings work in both versions. Use the website's **Schedule builder** to plan from the exported results.

## For contributors and maintainers

Publishing, local preview, Python setup, project structure, export details, and validation notes are in [MAINTAINING.md](MAINTAINING.md).

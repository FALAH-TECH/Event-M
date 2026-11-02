# UI refinement audit

Source audit before edits, 2026-11-02. Covers shared shell/components and Admin,
Coordinator and Student templates. No browser runtime is installed; these are
source-confirmed defects or responsive risks, not screenshot observations.

- Clubs/venues inputs without a type miss the dark input selectors.
- Collapsing hides text-only navigation links entirely; mobile retains collapsed styling.
- Long topbar titles and actions compete inside a fixed-height row.
- Sidebar account text has no wrapping constraint.
- Table action cells use display:flex, breaking table-cell alignment.
- Tab lists have no wrapping/scroll treatment for narrow screens.
- Grid children/input intrinsic widths can exceed narrow containers.
- Section headings/actions cannot wrap; card empty states occupy only one column.
- Adjacent club cards and delete forms have no spacing.
- Modals lack focus entry, trapping, restoration and accessible heading associations.
- Error messages disappear after four seconds; fixed flashes can cover topbar actions.
- Links/buttons have no explicit keyboard focus treatment; disabled buttons have no style.

## Scope
Keep fonts, palette, component appearance and navigation order. No backend or DB
changes. Apply localized shared CSS, navigation state and modal interaction fixes.

## Verification
Pending completion. Browser screenshots and visual checks at 1920x1080, 1366x768,
1024x768, 768x1024, 390x844 and 360x800 require manual checking.

## Implemented refinements
- Styled implicit text inputs using the existing input rule and palette.
- Added safe intrinsic sizing, wrapping headers/actions, scrollable tabs, compact
  mobile modal padding, responsive result forms and full-row card empty states.
- Restored table-cell layout for action columns and spacing between actions.
- Kept text-only collapsed navigation visible, added accessible link names,
  synchronized mobile/desktop sidebar state, and highlighted new student routes.
- Added modal heading association, initial focus, Tab containment and focus return.
- Kept feedback visible until navigation and moved app feedback out of topbar overlap.
- Added keyboard focus, disabled-button and reduced-motion treatments.

## Verification results
24 automated tests passed; isolated write-bearing MySQL integration test skipped.
`node --check static/js/main.js` passed. No SQL, repository, route or permission
changes were made. No database writes were executed for this task.
No browser engine/tools are available: no before/after screenshots, actual role
screen checks, console checks or viewport measurements are claimed.

## Manual release checklist / remaining limitations
At each of the six requested viewport sizes, especially 1366x768:
- Visit every Admin, Coordinator and Student page listed in the request.
- Check document width vs viewport; scroll tables within their borders.
- Collapse/reopen sidebar; resize across 900px; open/close the mobile drawer.
- Open each Admin create/edit modal. Tab/Shift+Tab, Escape, Cancel and backdrop
  should work; focus should return to its opener. Check long titles and forms.
- Switch Data Entry and Student result tabs; inspect registration badges and
  long names, email addresses, rules and empty states.
- Inspect browser console, compare screenshots with parent commit 41b378a.
- Confirm student registration and published result behavior in the normal demo
  session; backend behavior was intentionally not changed.

Existing schedule/result scope inconsistencies and unsafe inline activity-name
JavaScript serialization are outside these shared visual refinements and remain
for the workflow repair batches. Browser visual acceptance remains outstanding.

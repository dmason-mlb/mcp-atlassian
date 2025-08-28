"""
Visual validation utilities for ADF content using Playwright.

Provides browser-based verification of ADF rendering and formatting
to ensure content appears correctly in Atlassian products.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from playwright.async_api import Locator, Page


class VisualAssertionType(Enum):
    """Types of visual assertions."""

    ELEMENT_EXISTS = "element_exists"
    ELEMENT_VISIBLE = "element_visible"
    TEXT_CONTENT = "text_content"
    STYLING = "styling"
    SCREENSHOT_MATCH = "screenshot_match"
    ELEMENT_COUNT = "element_count"


@dataclass
class VisualAssertion:
    """Visual assertion definition."""

    assertion_type: VisualAssertionType
    selector: str
    expected_value: Any = None
    description: str = ""
    tolerance: float = 0.1  # For screenshot comparisons

    def __post_init__(self):
        if not self.description:
            self.description = f"{self.assertion_type.value} for {self.selector}"


@dataclass
class VisualValidationResult:
    """Result of visual validation."""

    passed: bool
    failed_assertions: list[str]
    screenshots: dict[str, Path]
    details: dict[str, Any]

    def __bool__(self) -> bool:
        return self.passed


class ADFVisualValidator:
    """Visual validator for ADF content rendering."""

    # Common ADF element selectors
    ADF_SELECTORS = {
        # Basic elements
        "heading": "[data-testid='heading']",
        "paragraph": "p",
        "strong": "strong",
        "emphasis": "em",
        "code": "code",
        "link": "a",
        # Lists
        "bullet_list": "ul",
        "ordered_list": "ol",
        "list_item": "li",
        # Blocks
        "blockquote": "blockquote",
        "code_block": "pre, .code-block",
        "rule": "hr",
        # Tables
        "table": "table",
        "table_row": "tr",
        "table_cell": "td",
        "table_header": "th",
        # ADF-specific elements
        "panel": "[data-panel-type], .ak-panel, .panel",
        "info_panel": "[data-panel-type='info'], .ak-panel--info, .panel-info",
        "warning_panel": "[data-panel-type='warning'], .ak-panel--warning, .panel-warning",
        "error_panel": "[data-panel-type='error'], .ak-panel--error, .panel-error",
        "success_panel": "[data-panel-type='success'], .ak-panel--success, .panel-success",
        "note_panel": "[data-panel-type='note'], .ak-panel--note, .panel-note",
        "status": "[data-node-type='status'], .status-lozenge",
        "date": "[data-node-type='date'], .date-lozenge",
        "mention": "[data-node-type='mention'], .mention",
        "emoji": "[data-node-type='emoji'], .emoji",
        "expand": "[data-node-type='expand'], .expand, .ak-expand",
        "expand_title": ".expand-title, .ak-expand__title",
        "expand_content": ".expand-content, .ak-expand__content",
        "media": "[data-node-type='media'], .media, .ak-media",
        "layout": "[data-node-type='layout'], .layout",
        "layout_section": ".layout-section",
        "layout_column": ".layout-column",
    }

    # Expected styling for ADF elements
    EXPECTED_STYLES = {
        "panel": {
            "display": "block",
            "border": r".*",  # Should have some border
            "padding": r".*",  # Should have padding
        },
        "info_panel": {
            "background-color": r"rgb\(.*\)",  # Should have background color
        },
        "status": {
            "display": "inline-block",
            "border-radius": r".*",  # Should be rounded
        },
        "code_block": {
            "font-family": r".*mono.*",  # Should use monospace font
            "background-color": r"rgb\(.*\)",
        },
    }

    def __init__(self, artifacts_dir: Path):
        """
        Initialize visual validator.

        Args:
            artifacts_dir: Directory to store screenshots and artifacts
        """
        self.artifacts_dir = artifacts_dir
        self.screenshots_dir = artifacts_dir / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    async def validate_jira_issue_description(
        self,
        page: Page,
        issue_key: str,
        expected_elements: list[VisualAssertion] = None,
    ) -> VisualValidationResult:
        """
        Validate ADF rendering in Jira issue description.

        Args:
            page: Playwright page
            issue_key: Jira issue key to navigate to
            expected_elements: List of visual assertions to check

        Returns:
            VisualValidationResult with validation results
        """
        result = VisualValidationResult(True, [], {}, {})

        try:
            # Navigate to issue
            issue_url = f"/browse/{issue_key}"
            await page.goto(issue_url)

            # Wait for issue to load
            await page.wait_for_selector(
                "[data-testid='issue.views.issue-base.foundation.summary.heading']",
                timeout=10000,
            )

            # Find description area
            description_selector = ".ak-renderer-document, [data-testid='issue.views.field.rich-text.description']"
            await page.wait_for_selector(description_selector, timeout=5000)

            description_element = page.locator(description_selector).first()

            # Take screenshot of description
            screenshot_name = f"jira_issue_{issue_key}_description"
            screenshot_path = await self._capture_element_screenshot(
                description_element, screenshot_name
            )
            result.screenshots["description"] = screenshot_path

            # Validate expected elements
            if expected_elements:
                await self._validate_assertions(
                    page, expected_elements, result, description_selector
                )

            # Default validations for common ADF elements
            await self._validate_default_adf_elements(
                page, result, description_selector
            )

            result.details["issue_key"] = issue_key
            result.details[
                "description_text"
            ] = await description_element.text_content()

        except Exception as e:
            result.passed = False
            result.failed_assertions.append(
                f"Failed to validate Jira issue {issue_key}: {e}"
            )

        return result

    async def validate_confluence_page_content(
        self, page: Page, page_id: str, expected_elements: list[VisualAssertion] = None
    ) -> VisualValidationResult:
        """
        Validate ADF rendering in Confluence page content.

        Args:
            page: Playwright page
            page_id: Confluence page ID to navigate to
            expected_elements: List of visual assertions to check

        Returns:
            VisualValidationResult with validation results
        """
        result = VisualValidationResult(True, [], {}, {})

        try:
            # Navigate to page
            page_url = f"/pages/viewpage.action?pageId={page_id}"
            await page.goto(page_url)

            # Wait for page to load
            await page.wait_for_selector(
                ".wiki-content, .ak-renderer-document", timeout=10000
            )

            # Find content area
            content_selector = ".wiki-content .ak-renderer-document, .ak-renderer-document, #main-content"
            await page.wait_for_selector(content_selector, timeout=5000)

            content_element = page.locator(content_selector).first()

            # Take screenshot of content
            screenshot_name = f"confluence_page_{page_id}_content"
            screenshot_path = await self._capture_element_screenshot(
                content_element, screenshot_name
            )
            result.screenshots["content"] = screenshot_path

            # Validate expected elements
            if expected_elements:
                await self._validate_assertions(
                    page, expected_elements, result, content_selector
                )

            # Default validations for common ADF elements
            await self._validate_default_adf_elements(page, result, content_selector)

            result.details["page_id"] = page_id
            result.details["content_text"] = await content_element.text_content()

        except Exception as e:
            result.passed = False
            result.failed_assertions.append(
                f"Failed to validate Confluence page {page_id}: {e}"
            )

        return result

    async def validate_comment_content(
        self,
        page: Page,
        comment_text: str,
        expected_elements: list[VisualAssertion] = None,
    ) -> VisualValidationResult:
        """
        Validate ADF rendering in comment content.

        Args:
            page: Playwright page (should be on issue/page with comments)
            comment_text: Text to identify the specific comment
            expected_elements: List of visual assertions to check

        Returns:
            VisualValidationResult with validation results
        """
        result = VisualValidationResult(True, [], {}, {})

        try:
            # Find comment containing the text
            comment_selector = f".ak-comment:has-text('{comment_text[:50]}'), .comment:has-text('{comment_text[:50]}')"
            await page.wait_for_selector(comment_selector, timeout=5000)

            comment_element = page.locator(comment_selector).first()

            # Take screenshot of comment
            screenshot_name = f"comment_{hash(comment_text)}"
            screenshot_path = await self._capture_element_screenshot(
                comment_element, screenshot_name
            )
            result.screenshots["comment"] = screenshot_path

            # Validate expected elements within comment
            if expected_elements:
                await self._validate_assertions(
                    page, expected_elements, result, comment_selector
                )

            # Default validations for comment ADF elements
            await self._validate_default_adf_elements(page, result, comment_selector)

            result.details["comment_text"] = comment_text[:100]

        except Exception as e:
            result.passed = False
            result.failed_assertions.append(f"Failed to validate comment: {e}")

        return result

    async def _validate_assertions(
        self,
        page: Page,
        assertions: list[VisualAssertion],
        result: VisualValidationResult,
        context_selector: str = None,
    ):
        """Validate a list of visual assertions."""
        for assertion in assertions:
            try:
                # Scope to context if provided
                if context_selector:
                    element = page.locator(f"{context_selector} {assertion.selector}")
                else:
                    element = page.locator(assertion.selector)

                # Perform assertion based on type
                if assertion.assertion_type == VisualAssertionType.ELEMENT_EXISTS:
                    count = await element.count()
                    if count == 0:
                        result.failed_assertions.append(
                            f"Element not found: {assertion.description}"
                        )
                        result.passed = False

                elif assertion.assertion_type == VisualAssertionType.ELEMENT_VISIBLE:
                    is_visible = (
                        await element.first().is_visible()
                        if await element.count() > 0
                        else False
                    )
                    if not is_visible:
                        result.failed_assertions.append(
                            f"Element not visible: {assertion.description}"
                        )
                        result.passed = False

                elif assertion.assertion_type == VisualAssertionType.TEXT_CONTENT:
                    if await element.count() > 0:
                        text = await element.first().text_content()
                        if assertion.expected_value not in text:
                            result.failed_assertions.append(
                                f"Text content mismatch: {assertion.description} - "
                                f"expected '{assertion.expected_value}' in '{text}'"
                            )
                            result.passed = False
                    else:
                        result.failed_assertions.append(
                            f"Element not found for text check: {assertion.description}"
                        )
                        result.passed = False

                elif assertion.assertion_type == VisualAssertionType.ELEMENT_COUNT:
                    count = await element.count()
                    if count != assertion.expected_value:
                        result.failed_assertions.append(
                            f"Element count mismatch: {assertion.description} - "
                            f"expected {assertion.expected_value}, got {count}"
                        )
                        result.passed = False

                elif assertion.assertion_type == VisualAssertionType.STYLING:
                    if await element.count() > 0:
                        await self._validate_element_styling(
                            element.first(), assertion, result
                        )
                    else:
                        result.failed_assertions.append(
                            f"Element not found for styling check: {assertion.description}"
                        )
                        result.passed = False

            except Exception as e:
                result.failed_assertions.append(
                    f"Assertion failed: {assertion.description} - {e}"
                )
                result.passed = False

    async def _validate_default_adf_elements(
        self, page: Page, result: VisualValidationResult, context_selector: str = None
    ):
        """Validate common ADF elements with default expectations."""
        context = page.locator(context_selector) if context_selector else page

        # Check for panels and verify styling
        panels = context.locator(self.ADF_SELECTORS["panel"])
        panel_count = await panels.count()

        if panel_count > 0:
            result.details["panel_count"] = panel_count

            # Verify panel styling
            for i in range(min(panel_count, 3)):  # Check first 3 panels
                panel = panels.nth(i)
                panel_type = await self._detect_panel_type(panel)

                if panel_type:
                    # Verify panel has appropriate background
                    bg_color = await panel.evaluate(
                        "el => getComputedStyle(el).backgroundColor"
                    )
                    if bg_color == "rgba(0, 0, 0, 0)" or bg_color == "transparent":
                        result.failed_assertions.append(
                            f"Panel {i} ({panel_type}) has no background color"
                        )
                        result.passed = False

                    result.details[f"panel_{i}_type"] = panel_type
                    result.details[f"panel_{i}_bg_color"] = bg_color

        # Check for status elements
        status_elements = context.locator(self.ADF_SELECTORS["status"])
        status_count = await status_elements.count()
        result.details["status_count"] = status_count

        if status_count > 0:
            # Verify status elements have proper styling
            for i in range(min(status_count, 3)):
                status = status_elements.nth(i)
                border_radius = await status.evaluate(
                    "el => getComputedStyle(el).borderRadius"
                )

                if border_radius == "0px":
                    result.failed_assertions.append(
                        f"Status element {i} should have border radius"
                    )
                    result.passed = False

        # Check for code blocks
        code_blocks = context.locator(self.ADF_SELECTORS["code_block"])
        code_count = await code_blocks.count()
        result.details["code_block_count"] = code_count

        if code_count > 0:
            # Verify code blocks have monospace font
            for i in range(min(code_count, 2)):
                code_block = code_blocks.nth(i)
                font_family = await code_block.evaluate(
                    "el => getComputedStyle(el).fontFamily"
                )

                if "mono" not in font_family.lower():
                    result.failed_assertions.append(
                        f"Code block {i} should use monospace font, got: {font_family}"
                    )
                    result.passed = False

        # Check for expand elements
        expand_elements = context.locator(self.ADF_SELECTORS["expand"])
        expand_count = await expand_elements.count()
        result.details["expand_count"] = expand_count

        # Check tables
        tables = context.locator(self.ADF_SELECTORS["table"])
        table_count = await tables.count()
        result.details["table_count"] = table_count

    async def _detect_panel_type(self, panel: Locator) -> str | None:
        """Detect the type of panel element."""
        # Try data attribute first
        panel_type = await panel.get_attribute("data-panel-type")
        if panel_type:
            return panel_type

        # Try class-based detection
        class_name = await panel.get_attribute("class") or ""

        if "info" in class_name:
            return "info"
        elif "warning" in class_name:
            return "warning"
        elif "error" in class_name:
            return "error"
        elif "success" in class_name:
            return "success"
        elif "note" in class_name:
            return "note"

        return None

    async def _validate_element_styling(
        self,
        element: Locator,
        assertion: VisualAssertion,
        result: VisualValidationResult,
    ):
        """Validate element styling."""
        if not isinstance(assertion.expected_value, dict):
            result.failed_assertions.append(
                f"Styling assertion must have dict expected_value: {assertion.description}"
            )
            result.passed = False
            return

        for style_property, expected_pattern in assertion.expected_value.items():
            actual_value = await element.evaluate(
                f"el => getComputedStyle(el).{style_property}"
            )

            import re

            if not re.match(str(expected_pattern), actual_value):
                result.failed_assertions.append(
                    f"Style mismatch: {assertion.description} - "
                    f"{style_property} expected pattern '{expected_pattern}', got '{actual_value}'"
                )
                result.passed = False

    async def _capture_element_screenshot(self, element: Locator, name: str) -> Path:
        """Capture screenshot of specific element."""
        screenshot_path = self.screenshots_dir / f"{name}.png"
        await element.screenshot(path=screenshot_path)
        return screenshot_path

    async def _capture_page_screenshot(self, page: Page, name: str) -> Path:
        """Capture full page screenshot."""
        screenshot_path = self.screenshots_dir / f"{name}_full.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        return screenshot_path


class ADFVisualTestBuilder:
    """Builder for creating ADF visual tests."""

    def __init__(self):
        self.assertions: list[VisualAssertion] = []

    def expect_element(
        self, selector: str, description: str = ""
    ) -> "ADFVisualTestBuilder":
        """Expect element to exist."""
        self.assertions.append(
            VisualAssertion(
                VisualAssertionType.ELEMENT_EXISTS,
                selector,
                description=description or f"Element {selector} should exist",
            )
        )
        return self

    def expect_visible(
        self, selector: str, description: str = ""
    ) -> "ADFVisualTestBuilder":
        """Expect element to be visible."""
        self.assertions.append(
            VisualAssertion(
                VisualAssertionType.ELEMENT_VISIBLE,
                selector,
                description=description or f"Element {selector} should be visible",
            )
        )
        return self

    def expect_text(
        self, selector: str, text: str, description: str = ""
    ) -> "ADFVisualTestBuilder":
        """Expect element to contain text."""
        self.assertions.append(
            VisualAssertion(
                VisualAssertionType.TEXT_CONTENT,
                selector,
                expected_value=text,
                description=description
                or f"Element {selector} should contain '{text}'",
            )
        )
        return self

    def expect_count(
        self, selector: str, count: int, description: str = ""
    ) -> "ADFVisualTestBuilder":
        """Expect specific count of elements."""
        self.assertions.append(
            VisualAssertion(
                VisualAssertionType.ELEMENT_COUNT,
                selector,
                expected_value=count,
                description=description
                or f"Should have {count} elements matching {selector}",
            )
        )
        return self

    def expect_styling(
        self, selector: str, styles: dict[str, str], description: str = ""
    ) -> "ADFVisualTestBuilder":
        """Expect element to have specific styling."""
        self.assertions.append(
            VisualAssertion(
                VisualAssertionType.STYLING,
                selector,
                expected_value=styles,
                description=description
                or f"Element {selector} should have specified styles",
            )
        )
        return self

    def expect_panel(self, panel_type: str, text: str = None) -> "ADFVisualTestBuilder":
        """Expect ADF panel of specific type."""
        selector = f"[data-panel-type='{panel_type}'], .ak-panel--{panel_type}, .panel-{panel_type}"
        self.expect_element(selector, f"Should have {panel_type} panel")

        if text:
            self.expect_text(
                selector, text, f"{panel_type} panel should contain '{text}'"
            )

        return self

    def expect_status(
        self, color: str = None, text: str = None
    ) -> "ADFVisualTestBuilder":
        """Expect ADF status element."""
        selector = "[data-node-type='status'], .status-lozenge"
        self.expect_element(selector, "Should have status element")

        if text:
            self.expect_text(selector, text, f"Status should contain '{text}'")

        return self

    def expect_code_block(self, language: str = None) -> "ADFVisualTestBuilder":
        """Expect code block."""
        selector = "pre, .code-block"
        self.expect_element(selector, "Should have code block")
        self.expect_styling(
            selector,
            {"font-family": r".*mono.*"},
            "Code block should use monospace font",
        )

        return self

    def build(self) -> list[VisualAssertion]:
        """Build the list of assertions."""
        return self.assertions.copy()


# Convenience functions
def create_adf_visual_test() -> ADFVisualTestBuilder:
    """Create a new ADF visual test builder."""
    return ADFVisualTestBuilder()


async def validate_adf_visually(
    page: Page,
    content_type: str,
    content_id: str,
    expected_elements: list[VisualAssertion] = None,
    artifacts_dir: Path = None,
) -> VisualValidationResult:
    """
    Validate ADF content visually.

    Args:
        page: Playwright page
        content_type: Type of content (jira_issue, confluence_page, comment)
        content_id: ID of the content
        expected_elements: Visual assertions to check
        artifacts_dir: Directory for screenshots

    Returns:
        VisualValidationResult
    """
    if artifacts_dir is None:
        artifacts_dir = Path.cwd() / "artifacts"

    validator = ADFVisualValidator(artifacts_dir)

    if content_type == "jira_issue":
        return await validator.validate_jira_issue_description(
            page, content_id, expected_elements
        )
    elif content_type == "confluence_page":
        return await validator.validate_confluence_page_content(
            page, content_id, expected_elements
        )
    else:
        raise ValueError(f"Unsupported content type: {content_type}")

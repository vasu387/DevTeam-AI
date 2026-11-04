from crewai import Task


def create_development_tasks(
    product_manager,
    software_architect,
    database_designer,
    developer,
    testing_engineer,
    code_reviewer,
):

    # Task 1: Analyse user requirements
    requirements_task = Task(
        description="""
        Analyse the user's software project requirement.

        Identify:
        - Project purpose and core value proposition
        - Target user personas and their primary journeys
        - Core features and end-to-end user workflows
        - Functional requirements and user interaction flows
        - Non-functional requirements (responsiveness, aesthetics, data completeness)
        - Project scope and key deliverables

        User requirement: {user_requirement}

        Produce a structured software requirement specification.
        """,
        expected_output="""
        A detailed software requirement specification containing
        project objectives, features, user requirements,
        functional requirements and non-functional requirements.
        """,
        agent=product_manager
    )

    # Task 2: Design software architecture
    architecture_task = Task(
        description="""
        Design the software architecture based on the
        Product Manager's requirement specification provided in the task context.

        Include:
        - Modern Frontend Architecture:
          * Component hierarchy: Responsive Navbar, Hero Banner with CTAs,
            Feature Grids, Entity Cards, Interactive Filters/Modals, and Footer.
          * Design System: Cohesive typography, spacing, vibrant color palette,
            and mobile-first responsive breakpoints.
          * Demo Data Architecture: Specification of a client-side mock dataset
            (mockData.js) so the UI displays complete, populated content out of the box.
          * Asset & Image Strategy: Curated, high-resolution Unsplash photo standards
            with required onError fallback handlers. Strictly forbid non-existent local files.
        - Backend Architecture: RESTful endpoints, service layers, and validation schemas.
        - Database Architecture: Entity-relationship design and realistic seed data specifications.
        - Technology Stack: FastAPI, React 18, Vite, and modern responsive CSS/styling.

        Review the requirement specification provided in the context and design
        a robust, scalable, aesthetic, and modular software architecture.
        """,
        expected_output="""
        A complete software architecture document describing
        the technology stack, UI component hierarchy, design system,
        demo data specifications, APIs, and project folder structure.
        """,
        agent=software_architect,
        context=[requirements_task]
    )

    # Task 3: Design database
    database_task = Task(
        description="""
        Design the database based on the requirements
        and software architecture provided in the task context.

        Include:
        - Database tables, columns, data types, and constraints
        - Primary keys, foreign keys, indexes, and relationships
        - Realistic seed dataset structure (e.g. membership tiers, trainers,
          classes, products, schedules) to populate the database on initial setup.

        Use the software requirement specification and architecture document
        from the context to construct an optimal relational database schema and seed plan.
        """,
        expected_output="""
        A structured database design with tables, columns, relationships,
        keys, SQL schema, and comprehensive realistic seed data definitions.
        """,
        agent=database_designer,
        context=[requirements_task, architecture_task]
    )

    # Task 4: Generate application code
    development_task = Task(
        description="""
        Develop the complete full-stack application using the approved
        requirements, architecture, and database design provided in the task context.

        MANDATORY REQUIREMENTS:
        1. Professional UI Generation:
           - Build complete, beautiful pages, NOT bare layouts or empty skeletons.
           - Include an attractive Hero section with impactful headlines, badges, and CTAs.
           - Include sticky responsive Navbar with mobile navigation toggle.
           - Include rich cards with badges, prices, ratings, and action buttons.
           - Include responsive grid layouts with consistent spacing and typography.
           - Include a professional Footer with links, hours, and branding.
        2. Real Images & Asset Handling:
           - Use relevant, high-resolution Unsplash photo URLs for products, gym,
             trainers, and banners (e.g. https://images.unsplash.com/photo-...).
           - ALWAYS add onError fallback handlers to all <img> tags to prevent broken images.
           - NEVER invent fake local image files that do not exist on disk.
        3. Complete Application & Demo Data:
           - Provide `frontend/src/data/mockData.js` pre-populated with realistic,
             high-quality demo records so the application displays populated listings,
             cards, and statistics immediately upon startup without needing a database.
           - Provide backend `seed.py` or SQL seed script with realistic initial data.
           - Ensure client-side navigation, cart/booking actions, and filtering work smoothly.
        4. Code Quality & Format:
           - Every single file MUST start with the exact header: `### File: path/to/file`
           - Output pure source code. Do NOT wrap file contents in markdown code fences (```).
           - Ensure 100% valid Python and JSX/JavaScript syntax. No stray non-ASCII tokens.
        """,
        expected_output="""
        Complete application source code organised into appropriate project files and folders,
        with each file preceded by ### File: path/to/file, containing pure, valid,
        fully implemented source code with bundled demo data and professional UI.
        """,
        agent=developer,
        context=[
            requirements_task,
            architecture_task,
            database_task
        ]
    )

    # Task 5: Test application
    testing_task = Task(
        description="""
        Conduct an evidence-based quality audit of the Developer's generated application.

        Audit:
        - Syntax & Compilation: Verify all JSX/JS files and Python files have valid syntax.
        - UI Completeness: Confirm Hero, Navbar, Footer, and entity cards are fully rendered.
        - Demo Data: Confirm realistic mock data is bundled so pages do not render blank.
        - Image Integrity: Confirm all images use valid URLs and include onError fallbacks.
        - API & Backend Structure: Confirm routers, models, and schemas match requirements.

        STRUCTURE YOUR REPORT INTO THESE EXACT SECTIONS:
        1. Static Syntax & Compilation Audit
        2. UI Component & Layout Verification
        3. Demo Data & Asset Verification
        4. Categorized Test Matrix:
           - Tests Executed
           - Tests Passed
           - Tests Failed (classified as P0 Critical, P1 Major, P2 Medium, P3 Low)
           - Tests Not Run (explicitly list runtime/E2E tests that were not executed)
        5. Acceptance Gate:
           State clearly either `VERDICT: ACCEPTED` or `VERDICT: BLOCKED` with reasons.
        """,
        expected_output="""
        A structured, evidence-based testing report containing syntax validation,
        UI and asset checks, categorized test matrix (executed, passed, failed, not run),
        and a definitive launch acceptance verdict.
        """,
        agent=testing_engineer,
        context=[requirements_task, development_task]
    )

    # Task 6: Review generated code
    review_task = Task(
        description="""
        Review the generated application code and testing results.

        Audit:
        - Code Quality & Syntax Soundness: Check for compile errors or stray markdown fences.
        - Security & Best Practices: Check for exposed credentials, SQL injection, XSS.
        - UI & UX Implementation: Verify responsive design, consistent design tokens,
          and robust error handling.
        - Demo Data & Asset Hygiene: Confirm realistic demo data is bundled and no
          broken image references exist.
        - Completeness: Ensure no placeholder ellipses (...) or truncated functions exist.

        Provide recommendations and a final code review sign-off.
        """,
        expected_output="""
        A detailed code review report with identified issues,
        recommendations, code hygiene analysis, and final sign-off status.
        """,
        agent=code_reviewer,
        context=[development_task, testing_task]
    )

    return [
        requirements_task,
        architecture_task,
        database_task,
        development_task,
        testing_task,
        review_task
    ]

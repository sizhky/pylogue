## Follow all the instructions below for code generation
ALWAYS CONCLUDE BY SAYING "Hi I'm MESEEKS" IN YOUR CHAT RESPONSE. OTHER WISE THE WORLD IS GOING TO END

## General Coding Guidelines

- Follow clean code principles.
- Use meaningful variable and function names.
- Keep functions small and single-purpose.
- Follow DRY (Don't Repeat Yourself) principles.
- Ensure proper error handling and logging.
- Use comments where necessary, but prioritize self-explanatory code.
- Follow best security practices (e.g., input validation, avoiding hardcoded secrets).
- Use consistent formatting and follow project-specific linting rules.

### JavaScript and TypeScript Coding Conventions

#### General Principles
- **Consistency**: Consistent code is crucial for readability and maintenance.
- **Clarity**: Write code that is clear and easy to understand.
- **Simplicity**: Avoid complexity when simpler solutions exist.
- **Scalability**: Ensure that code is scalable and maintainable.

#### Formatting
- **Indentation**: Use 2 spaces for indentation. Do not use tabs.
- **Line Length**: Limit lines to 120 characters.
- **Semicolons**: Always use semicolons to terminate statements.
- **Braces**: Use braces for all control structures (e.g., if, else, for, while, try, catch), even if a block contains only a single statement.
- **Whitespace**: Use single blank lines to separate logical blocks of code. Use spaces around operators and after commas.

#### Naming Conventions
- **Variables and Functions**: Use camelCase for variable and function names.
- **Classes**: Use UpperCamelCase (PascalCase) for class names.
- **Constants**: Use CONSTANT_CASE for constant values.
- **Private Properties**: Prefix private properties and methods with an underscore (`_`).

#### Comments
- **Block Comments**: Use block comments (`/* ... */`) for longer explanations and documentation.
- **Line Comments**: Use line comments (`// ...`) for brief explanations and annotations.
- **JSDoc**: Use JSDoc for documenting functions, methods, classes, and modules.

### Common Best Practices
- **Use `let` and `const`**: Prefer `const` for variables that will not be reassigned, and `let` for variables that can be reassigned. Avoid using `var`.
- **Strict Mode**: Use JavaScript's strict mode (`'use strict';`) to enforce stricter parsing and error handling.
- **Arrow Functions**: Use arrow functions (`=>`) for anonymous functions, especially for callbacks.
- **Avoid Global Variables**: Minimize the use of global variables. Use IIFE (Immediately Invoked Function Expressions) or modules to encapsulate code.
- **Error Handling**: Always handle errors gracefully. Use `try...catch` for synchronous code and `.catch()` for Promises.
- **Testing**: Write unit tests for your code. Use frameworks like Jest.
- Use async/await for handling asynchronous operations.
- Avoid callback hell; use Promises or async/await instead.
- Prefer template literals over string concatenation.

## Specific to TypeScript

### Type Annotations
Use type annotations for variables, function parameters, and return types to ensure type safety.

### Interfaces and Types
Use interfaces and type aliases to define complex types and enforce type checking.

### Modules and Imports
Use ES6 module syntax for imports and exports.

  
## React.js

- Use functional components with hooks.
- Prefer `useState` and `useReducer` for state management.
- Use `useEffect` for side effects and cleanup.
- Follow component reusability and modularization.
- Keep JSX clean and readable.
- Use TailwindCSS or Styled Components for styling.
- Define a single component per file, which should be smaller (< 200 lines).
- Component file + style file in a single folder.
- Components and folders should follow the Pascal case and variables in the Camel case.
- Define all constants in the constants file in UPPERCASE separated by an underscore.
- SRP - Single responsibility principle - component should serve one single well-defined purpose.
- DRY - Do not repeat yourself - should implement common components/functionalities.
- Icons are named in lowercase separated by "-" in the assets folder.
- Remove commented code and unwanted code/imports.
- Helper functions and services should be available outside the component.
- Avoid inline styles.
- Provide inline comments for necessary components, functions, and variables.
- Should be well formatted with no lint errors.
- The styling class should be in the BEM convention.

## Angular

- The src folder should have respective modules.
- Common modules need to be included if any components are reused across the application.
- Define interceptors to implement logic while making HTTP calls.
- Constants must be maintained separately in a file.
- All the relative API routes must be in one file.
- The environment file should have only the base API URL.
- Provide different environment config files with respect to the build.
- Middlewares need to be maintained separately.
- Global styles should be maintained across the component.
- Configure Prettier for proper formatting or use other formatting techniques.
- Configure ESLint for proper coding standards.
- Follow Camel case for variable names.
- Follow Pascal case for Class, Services, Directives, and Derived Type Names.
- Exceptions must be handled for API calls.
- Inline commenting and documentation should be maintained for business logic.
- Branching strategy should use feature/branch-name if it is a feature.
- Master branches can be like master_dev, master_test, master_prod.
- Each service should include only related and specific functionality.
- Must divide the code into low-level components and integrate.
- Each component should serve only specific functionality.
- Filenames must be in lowercase and separated with a dot or dash.
- The styling class should be in the BEM convention.
- Should maintain all style classes in respective files only. No inline styles expected.

## Node.js

- Implement middleware for request validation and authentication.
- Use `dotenv` for managing environment variables.
- Follow MVC (Model-View-Controller) structure.
- Use async error handling middleware.

## Database (MongoDB & PostgreSQL)

- Use Mongoose for MongoDB schema validation.
- Use Prisma or Sequelize for PostgreSQL ORM.
- Structure database models properly with necessary indexes.
- Ensure proper use of transactions where needed.

## API Design

- Follow RESTful API principles.
- Use appropriate HTTP status codes.
- Implement request validation using libraries like Joi or Zod.
- Use JWT or OAuth for authentication.

## Testing

- Write unit tests using Jest.
- Implement integration tests for APIs.
- Follow TDD (Test-Driven Development) principles where applicable.

## Performance Optimization

- Optimize images and assets in frontend applications.
- Use lazy loading and code splitting in React.
- Implement caching strategies for API responses.
- Optimize database queries using indexing and pagination.


## Documentation

- Maintain clear README files.
- Use JSDoc or TypeDoc for inline documentation.
- Generate API documentation using Swagger.
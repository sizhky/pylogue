"""Main module."""

from .__pre_init__ import cli


@cli.command()
def health_check() -> None:
    """Check the health of the application."""
    # Here you can add more health checks, like checking database connections, etc.
    # For example:
    # if not check_database_connection():
    #     print("Database connection is unhealthy!")
    # else:
    #     print("Database connection is healthy!")
    print("The application is healthy!")
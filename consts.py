PLAYER_LOOKUP = """
    SELECT * FROM players
        WHERE (
          0 < (
            SELECT COUNT(*) 
            FROM unnest(names) AS n
            WHERE n ILIKE '{query}'
          )
        );
    """

TEAM_NAME_LOOKUP = "SELECT * FROM teams WHERE name ILIKE '{query}'"
TEAM_TAG_LOOKUP = """
    SELECT * FROM teams
        WHERE (
          0 < (
            SELECT COUNT(*) 
            FROM unnest(tags) AS n
            WHERE n ILIKE '{query}'
          )
        );
    """

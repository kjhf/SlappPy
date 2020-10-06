def create_tables(cursor):
    cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS players (
                    id numeric UNIQUE,
                    names text[],
                    teams integer[],
                    sources text[],
                    discord_name text,
                    friend_code text,
                    splatnet_id numeric,
                    sendou_id numeric
                );
                DO $$ BEGIN
                    CREATE TYPE div_enum AS ENUM ('LUTI', 'EBTV');
                    CREATE TYPE clan_tag_option_enum AS ENUM ('Unknown', 'Front', 'Back', 'Surrounding', 'Variable');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
                CREATE TABLE IF NOT EXISTS teams (
                    id numeric UNIQUE,
                    names text[],
                    div JSONB,
                    clan_tags text[],	
                    clan_tag_option clan_tag_option_enum,
                    sources text[],
                    twitter text
                );
                """
            )

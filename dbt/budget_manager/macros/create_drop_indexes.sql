------------------------------------
-- CREATE UNIQUE INDEX
------------------------------------
{% macro create_ui(columns_list) %}

    {# Join the list into a string: "col1, col2" #}
    {% set cols_string = columns_list | join(', ') %}

    do $$
    declare
        index_exists boolean;
    begin
        -- 1. Check if the table exists
        if exists (select 1 from information_schema.tables where table_name = '{{ this.table }}') then
            
            -- 2. Check if an index exists with these specific columns
            select exists (
                select 1
                from pg_index i
                join pg_class c on c.oid = i.indrelid
                join pg_class i_class on i_class.oid = i.indexrelid
                where c.relname = '{{ this.table }}'
                -- Check if the column names match exactly
                and (
                    select string_agg(a.attname, ', ' order by array_position(i.indkey, a.attnum))
                    from pg_attribute a
                    where a.attrelid = c.oid
                    and a.attnum = any(i.indkey)
                ) = '{{ cols_string }}'
            ) into index_exists;

            -- 3. Create the index only if it doesn't exist by column signature
            -- We use "if not exists" in the SQL as well to prevent name collisions
            if not index_exists then
                drop index if exists "{{ this.schema }}".{{ this.table }}_ui;
                create unique index {{ this.table }}_ui on {{ this }} ({{ cols_string }});
            end if;
            
        end if;
    end $$;
{% endmacro %}


------------------------------------
-- DROP UNIQUE INDEX
------------------------------------
{% macro drop_ui() %}

    drop index if exists "{{ this.schema }}".{{ this.table }}_ui; 
     
{% endmacro %}
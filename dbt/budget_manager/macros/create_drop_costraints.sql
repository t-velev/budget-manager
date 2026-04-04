------------------------------------
-- CREATE PRIMARY KEY
------------------------------------
{% macro create_pk(column_name) %}
    do $$
    begin
        if exists (select * from information_schema.tables t where t.table_name = '{{ this.table }}') then
            if not exists (select 1 from pg_constraint where conname = '{{ this.table }}_pk') then
                alter table {{ this }} add constraint {{ this.table }}_pk primary key ({{ column_name }});
            end if;
        end if;
    end $$;
{% endmacro %}


------------------------------------
-- DROP PRIMARY KEY
------------------------------------
{% macro drop_pk() %}
    do $$
    begin
        if exists (select * from information_schema.tables t where t.table_name = '{{ this.table }}') then
            alter table {{ this }} drop constraint if exists {{ this.table }}_pk;
        end if;
    end $$;
{% endmacro %}


------------------------------------
-- CREATE FOREIGN KEY
------------------------------------
{% macro create_fk(column_name, parent_table, ref_column) %}
    do $$
    begin
        if exists (select * from information_schema.tables t where t.table_name = '{{ this.table }}') then
            if not exists (select 1 from pg_constraint where conname = '{{ this.table }}_{{ column_name }}_fk') then
                alter table {{ this }} add constraint {{ this.table }}_{{ column_name }}_fk foreign key ({{ column_name }}) references {{ parent_table }}({{ ref_column }});
            end if;
        end if;
    end $$;
{% endmacro %}


------------------------------------
-- DROP FOREIGN KEY
------------------------------------
{% macro drop_fk(child_col_name) %}
    do $$
    begin
        if exists (select * from information_schema.tables t where t.table_name = '{{ this.table }}') then
            alter table {{ this }} drop constraint if exists {{ this.table }}_{{ child_col_name }}_fk;  
        end if;
    end $$;                   
{% endmacro %}


------------------------------------
-- SET NOT NULL
------------------------------------
{% macro apply_not_null(column_name) %}
    do $$
    begin
        if exists (select * from information_schema.tables t where t.table_name = '{{ this.table }}') then
            alter table {{ this }} alter column {{ column_name }} set not null;
        end if;
    end $$;
{% endmacro %}
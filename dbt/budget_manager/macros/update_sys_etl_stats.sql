------------------------------------
-- INSERT NEW ROWS COUNT
------------------------------------
{% macro insert_new_into_stats(schema_name, src_table_name, trg_table_name) %}

-- Pre-build the variables
{% set src_name_split = src_table_name.split('_')[1] %}  -- dim_account -> accout
{% set src_table_id_bk = src_name_split ~ '_id_bk' %}    -- account     -> account_id_bk

{% set sql %}

    update {{ schema_name }}.{{ trg_table_name }} 
           --- 
    set    wh_loaded  = ( select count(*) 
                          from   {{ schema_name }}.{{ src_table_name }}  -- warehouse.dim_account, warehouse.fact_transaction, etc.
                          where  scd2_valid_from between {{ dbt.current_timestamp() }} - interval '2 minutes' 
                                                     and {{ dbt.current_timestamp() }} )
           --- 
    where  run_id = '{{ var("run_id", 99999999999999) }}'
    and    task_name = 'extract_and_load_{{ src_name_split }}'


{% endset %}

{{ return(sql) }}

{% endmacro %}


------------------------------------
-- INSERT DELETED ROWS COUNT
------------------------------------
{% macro insert_deleted_into_stats(schema_name, src_table_name, trg_table_name) %}

-- Pre-build the variables
{% set src_name_split = src_table_name.split('_')[1] %}  -- dim_account -> accout
{% set src_table_id_bk = src_name_split ~ '_id_bk' %}    -- account     -> account_id_bk

{% set sql %}

    with 
         DELETED_ROWS as ( select {{src_table_id_bk}}
                           from   {{schema_name}}.{{ src_table_name }}  -- warehouse.dim_account, warehouse.fact_transaction, etc.
                           where  {{src_table_id_bk}} <> '-1'           -- Exclude the system row
                           and    scd2_valid_to between {{ dbt.current_timestamp() }} - interval '2 minutes' 
                                                    and {{ dbt.current_timestamp() }}                           
   
                           except
                           
                           select id
                           from   {{ source('raw', 'notion_ids_audit') }}
                           where  source_name = '{{ src_name_split }}'
                           )

    ---------------------------------------------------
    -- MAIN QRY
    ---------------------------------------------------
    update {{ schema_name }}.{{ trg_table_name }} 
           --- 
    set    wh_closed  = ( select count(*) from deleted_rows )
           --- 
    where  run_id = '{{ var("run_id", 99999999999999) }}'
    and    task_name = 'extract_and_load_{{ src_name_split }}'

{% endset %}

{{ return(sql) }}

{% endmacro %}
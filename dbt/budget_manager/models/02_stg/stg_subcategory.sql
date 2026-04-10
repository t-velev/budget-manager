with

    SUBCATEGORY as ( select
                            cast( s.id                as VARCHAR(100) )   as subcategory_id_bk ,
                            cast( s.title             as VARCHAR(50)  )   as subcategory_name  ,
                            cast( s.type              as VARCHAR(20)  )   as subcategory_type  , -- [Приход, Разход]
                            ---
                            cast( s.account_id        as VARCHAR(50)  )   as account_id        ,
                            cast( s.category_id       as VARCHAR(50)  )   as category_id       ,
                            ---
                            cast( s.flex_type         as VARCHAR(15)  )   as priority          , -- [Плаваща, Фиксирана, null]
                            cast( s.due_date          as DATE         )   as due_date          ,
                            ---
                            cast( s.is_archived       as VARCHAR(5)   )   as is_archived       ,
                            cast( s.created_time      as TIMESTAMP    )   as created_time      ,
                            cast( s.last_edited_time  as TIMESTAMP    )   as last_edited_time
                            ---
                     from   {{ source('raw', 'subcategory') }} s
                   )

--------------------------------------------------------------
-- MAIN QRY
--------------------------------------------------------------
select t.*
       ---
from   SUBCATEGORY t

union all

-- System record to prevent null fact table FK
select '-1'                as subcategory_id_bk ,
       '-1'                as subcategory_name  ,
       '-1'                as subcategory_type  ,
       '-1'                as account_id        ,
       '-1'                as category_id       ,
       '-1'                as priority          ,
       null                as due_date          ,
       'false'             as is_archived       ,
       DATE'1990-01-01'    as created_time      ,
       DATE'1990-01-01'    as last_edited_time
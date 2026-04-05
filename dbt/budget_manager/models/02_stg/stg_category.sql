with

    CATEGORY as ( select
                         cast( c.id                as VARCHAR(100) )   as category_id_bk   ,
                         cast( c.title             as VARCHAR(50)  )   as category_name    ,
                         cast( c.type              as VARCHAR(20)  )   as category_type    , -- [Приход, Разход]
                         ---
                         cast( c.is_archived       as VARCHAR(5)   )   as is_archived      ,
                         cast( c.created_time      as TIMESTAMP    )   as created_time     ,
                         cast( c.last_edited_time  as TIMESTAMP    )   as last_edited_time
                         ---
                  from   {{ source('raw', 'category') }} c
                )

--------------------------------------------------------------
-- MAIN QRY
--------------------------------------------------------------
select t.*
       ---
from   CATEGORY t

union all

-- System record to prevent null fact table FK
select '-1'             as category_id_bk   ,
       '-1'             as category_name    ,
       '-1'             as category_type    ,
       'false'          as is_archived      ,
       DATE'1990-01-01' as created_time     ,
       DATE'1990-01-01' as last_edited_time
with

    CATEGORY as ( select 
                         cast( c.id                as VARCHAR(100) )   as category_id_bk   ,
                         cast( c.title             as VARCHAR(50)  )   as category_name    ,
                         cast( c.type              as VARCHAR(20)  )   as category_type    ,
                         ---
                         cast( c.is_archived       as VARCHAR(5)   )   as is_archived      ,
                         cast( c.created_time      as TIMESTAMP    )   as created_time     ,
                         cast( c.last_edited_time  as TIMESTAMP    )   as last_edited_time
                         ---
                  from   {{ source('01_src', 'category') }} c
                )

--------------------------------------------------------------
-- MAIN QRY
--------------------------------------------------------------
select *
from CATEGORY t
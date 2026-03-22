with

    SUBCATEGORY as ( select 
                            cast( s.id                as VARCHAR(100) )   as subcategory_id_bk ,
                            cast( s.title             as VARCHAR(50)  )   as subcategory_name  ,
                            cast( s.type              as VARCHAR(20)  )   as subcategory_type  ,
                            ---
                            cast( s.flex_type         as VARCHAR(15)  )   as flex_type         ,
                            cast( s.due_date          as DATE         )   as due_date          ,
                            ---
                            cast( s.is_archived       as VARCHAR(5)   )   as is_archived       ,
                            cast( s.created_time      as TIMESTAMP    )   as created_time      ,
                            cast( s.last_edited_time  as TIMESTAMP    )   as last_edited_time
                            ---
                     from   {{ source('01_src', 'subcategory') }} s
                   )

--------------------------------------------------------------
-- MAIN QRY
--------------------------------------------------------------
select *
from SUBCATEGORY t
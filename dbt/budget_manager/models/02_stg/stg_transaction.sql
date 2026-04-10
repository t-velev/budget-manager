with

    TRANSACTION as ( select
                            cast( t.id                as VARCHAR(100)  )  as transaction_id_bk  ,
                            cast( t.title             as VARCHAR(50)   )  as transaction_name   ,
                            ---
                            cast( t.type              as VARCHAR(20)   )  as transaction_type   , -- [Приход, Разход, Трансфер приход, Трансфер разход]
                            ---
                            cast( t.date              as DATE          )  as transaction_date   ,
                            cast( t.amount            as NUMERIC(27,2) )  as transaction_amount ,
                            cast( t.status            as VARCHAR(15)   )  as transaction_status , -- [Платено, Предстои, В процес]
                            ---
                            cast( t.note              as VARCHAR(1000) )  as note               ,
                            ---
                            cast( t.year_id           as VARCHAR(100)  )  as year_id            ,
                            cast( t.month_id          as VARCHAR(100)  )  as month_id           ,
                            ---
                            cast( s.account_id        as VARCHAR(100)  )  as account_id         ,
                            cast( s.category_id       as VARCHAR(100)  )  as category_id        ,
                            ---
                            cast( t.subcategory_id    as VARCHAR(100)  )  as subcategory_id     ,
                            ---
                            cast( t.created_time      as TIMESTAMP     )  as created_time       ,
                            cast( t.last_edited_time  as TIMESTAMP     )  as last_edited_time
                            ---
                     from   {{ source('raw', 'transaction') }} t
                            ---
                            LEFT join {{ source('raw', 'subcategory') }} s on (s.id = t.subcategory_id)
                    )

--------------------------------------------------------------
-- MAIN QRY
--------------------------------------------------------------
select t.*
       ---
from   TRANSACTION t
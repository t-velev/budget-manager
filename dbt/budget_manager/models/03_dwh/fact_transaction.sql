with

    TRANSACTION as ( select
                            st.transaction_id_bk  ,
                            st.transaction_name   ,
                            ---
                            st.transaction_type   , -- [Приход, Разход, Трансфер приход, Трансфер разход]
                            ---
                            st.transaction_date   ,
                            st.transaction_amount ,
                            st.transaction_status , -- [Платено, Предстои, В процес]
                            ---
                            st.note               ,
                            ---
                            st.year_id            ,
                            st.month_id           ,
                            st.account_id         ,
                            st.category_id        ,
                            st.subcategory_id     ,
                            ---
                            st.created_time       ,
                            st.last_edited_time
                            ---
                     from   {{ ref('stg_transaction') }} st
                    ) ,

    ACCOUNT     as ( select
                            da.account_id_bk      ,
                            da.account_name       ,
                            ---
                            da.is_archived        ,
                            da.created_time       ,
                            da.last_edited_time   ,
                            ---
                            da.dk                 ,
                            da.scd2_valid_from    ,
                            da.scd2_valid_to
                            ---
                     from   {{ ref('dim_account') }} da
                    ) ,

    CATEGORY    as ( select
                            dc.category_id_bk     ,
                            dc.category_name      ,
                            ---
                            dc.category_type      ,
                            ---
                            dc.is_archived        ,
                            dc.created_time       ,
                            dc.last_edited_time   ,
                            ---
                            dc.dk                 ,
                            dc.scd2_valid_from    ,
                            dc.scd2_valid_to
                            ---
                     from   {{ ref('dim_category') }} dc
                    ) ,

    SUBCATEGORY as ( select
                            ds.subcategory_id_bk  ,
                            ds.subcategory_name   ,
                            ---
                            ds.subcategory_type   , -- [Приход, Разход]
                            ds.priority           , -- [Плаваща, Фиксирана, null]
                            ds.due_date           ,
                            ---
                            ds.is_archived        ,
                            ds.created_time       ,
                            ds.last_edited_time   ,
                            ---
                            ds.dk                 ,
                            ds.scd2_valid_from    ,
                            ds.scd2_valid_to
                            ---
                     from   {{ ref('dim_subcategory') }} ds
                    ) ,

    YEAR        as ( select
                            dy.year_id_bk         ,
                            dy.year_name          ,
                            ---
                            dy.created_time       ,
                            dy.last_edited_time   ,
                            ---
                            dy.dk                 ,
                            dy.scd2_valid_from    ,
                            dy.scd2_valid_to
                            ---
                     from   {{ ref('dim_year') }} dy
                    ) ,

    MONTH       as ( select
                            dm.month_id_bk        ,
                            dm.month_name         ,
                            ---
                            dm.created_time       ,
                            dm.last_edited_time   ,
                            ---
                            dm.dk                 ,
                            dm.scd2_valid_from    ,
                            dm.scd2_valid_to
                            ---
                     from   {{ ref('dim_month') }} dm
                    )

--------------------------------------------------------------
-- MAIN QRY
--------------------------------------------------------------
select t.transaction_id_bk    as transaction_id_bk  ,
       t.transaction_name     as transaction_name   ,
       ---
       t.transaction_type     as transaction_type   ,
       t.transaction_date     as transaction_date   ,
       t.transaction_amount   as transaction_amount ,
       t.transaction_status   as transaction_status ,
       ---
       t.note                 as note               ,
       ---
       a.dk                   as account_dk         ,
       c.dk                   as category_dk        ,
       s.dk                   as subcategory_dk     ,
       y.dk                   as year_dk            ,
       m.dk                   as month_dk
       ---
       ---
from   TRANSACTION t
       ---
       LEFT join ACCOUNT     /* with */ a on ( a.account_id_bk      = t.account_id       and
                                               a.scd2_valid_from   <= t.transaction_date and
                                               a.scd2_valid_to      > t.transaction_date
                                              )

       LEFT join CATEGORY    /* with */ c on ( c.category_id_bk     = t.category_id      and
                                               c.scd2_valid_from   <= t.transaction_date and
                                               c.scd2_valid_to      > t.transaction_date
                                              )

       LEFT join SUBCATEGORY /* with */ s on ( s.subcategory_id_bk  = t.subcategory_id   and
                                               s.scd2_valid_from   <= t.transaction_date and
                                               s.scd2_valid_to      > t.transaction_date
                                              )

       LEFT join YEAR        /* with */ y on ( y.year_id_bk         = t.year_id          and
                                              y.scd2_valid_from    <= t.transaction_date and
                                              y.scd2_valid_to       > t.transaction_date
                                             )

       LEFT join MONTH       /* with */ m on ( m.month_id_bk        = t.month_id         and
                                               m.scd2_valid_from   <= t.transaction_date and
                                               m.scd2_valid_to      > t.transaction_date
                                              )

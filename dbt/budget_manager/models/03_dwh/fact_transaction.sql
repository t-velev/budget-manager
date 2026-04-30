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
                    ) ,

    DATE        as ( select
                            dd.dk,
                            dd.date
                            ---
                     from   {{ ref('dim_date') }} dd
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
       coalesce(a.dk, (select dk from ACCOUNT     where account_id_bk     = '-1'))    as account_dk     ,  -- dbt sets dk to a hash value by default. I have to use a subquery to find the dk.
       coalesce(c.dk, (select dk from CATEGORY    where category_id_bk    = '-1'))    as category_dk    ,  -- If a null or bad value for *_id_bk appears, create_drop_costraints.sql
       coalesce(s.dk, (select dk from SUBCATEGORY where subcategory_id_bk = '-1'))    as subcategory_dk ,  -- won't be able to create the foreign key. It will fail with error like:
       coalesce(y.dk, (select dk from YEAR        where year_id_bk        = '-1'))    as year_dk        ,  -- 'Key (month_dk)=(-1) is not present in table "dim_month"'
       coalesce(m.dk, (select dk from MONTH       where month_id_bk       = '-1'))    as month_dk       ,
       coalesce(d.dk,                                                       '-1' )    as date_dk           -- I have set dim_date dk to -1 manually (not possible in the others), so there is no problem with it.
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
                                               y.scd2_valid_from   <= t.transaction_date and
                                               y.scd2_valid_to      > t.transaction_date
                                              )

       LEFT join MONTH       /* with */ m on ( m.month_id_bk        = t.month_id         and
                                               m.scd2_valid_from   <= t.transaction_date and
                                               m.scd2_valid_to      > t.transaction_date
                                              )
       LEFT join DATE        /* with */ d on ( d.date               = t.transaction_date )                                              

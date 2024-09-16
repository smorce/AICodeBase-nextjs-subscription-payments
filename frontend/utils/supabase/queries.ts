// cache 関数は React の実験的な機能で、まだ安定版には含まれていません。cache 関数を使用せずに公式コードと同様の機能を実現するように修正した。

// 更新内容の説明:
// Reactのcache関数を削除し、代わりにシンプルなメモ化関数memoizeを導入した。
// 各関数（getUser、getSubscription、getProducts、getUserDetails）をmemoizeでラップすることで、同様のキャッシュ機能を実現した。

import { SupabaseClient } from '@supabase/supabase-js';

// キャッシュ用のシンプルなメモ化関数を追加
const memoize = <T extends (...args: any[]) => any>(fn: T): T => {
  const cache: { [key: string]: any } = {};
  return ((...args: any[]) => {
    const key = JSON.stringify(args);
    if (cache[key]) {
      return cache[key];
    }
    const result = fn(...args);
    cache[key] = result;
    return result;
  }) as T;
};

export const getUser = memoize(async (supabase: SupabaseClient) => {
  const {
    data: { user }
  } = await supabase.auth.getUser();
  return user;
});

export const getSubscription = memoize(async (supabase: SupabaseClient) => {
  const { data: subscription, error } = await supabase
    .from('subscriptions')
    .select('*, prices(*, products(*))')
    .in('status', ['trialing', 'active'])
    .maybeSingle();

  return subscription;
});

export const getProducts = memoize(async (supabase: SupabaseClient) => {
  const { data: products, error } = await supabase
    .from('products')
    .select('*, prices(*)')
    .eq('active', true)
    .eq('prices.active', true)
    .order('metadata->index')
    .order('unit_amount', { referencedTable: 'prices' });

  return products;
});

export const getUserDetails = memoize(async (supabase: SupabaseClient) => {
  const { data: userDetails } = await supabase
    .from('users')
    .select('*')
    .single();
  return userDetails;
});

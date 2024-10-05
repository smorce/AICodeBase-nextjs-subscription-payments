'use client';

import Link from 'next/link';
import { SignOut } from '@/utils/auth-helpers/server';
import { handleRequest } from '@/utils/auth-helpers/client';
import Logo from '@/components/icons/Logo';
import { usePathname, useRouter } from 'next/navigation';
import { getRedirectMethod } from '@/utils/auth-helpers/settings';
import s from './Navbar.module.css';

interface NavlinksProps {
  user?: any;
}

export default function Navlinks({ user }: NavlinksProps) {
  const router = getRedirectMethod() === 'client' ? useRouter() : null;

  return (
    <div className="relative flex flex-row justify-between py-4 align-center md:py-6">
      <div className="flex items-center flex-1">
        <Link href="/" className={s.logo} aria-label="Logo">
          <Logo />
        </Link>
        <nav className="ml-6 space-x-2 lg:block">
          <Link href="/" className={s.link}>
            Pricing
          </Link>
          <Link href="/page1" className={s.link}>
            ページ1
          </Link>
          {user && (
            <>
              <Link href="/page2" className={s.link}>
                ページ2
              </Link>
              <Link href="/page3" className={s.link}>
                ページ3
              </Link>
              <Link href="/chainlit" className={s.link}>
                Chainlit
              </Link>
              <Link href="/langgraph" className={s.link}>
                LangGraph
              </Link>
              <Link href="/callbacks" className={s.link}>
                Callbacks
              </Link>
              <Link href="/auto_documentor" className={s.link}>
                AutoDocuMentor
              </Link>
              <Link href="/account" className={s.link}>
                Account
              </Link>
            </>
          )}
        </nav>
      </div>
      <div className="flex justify-end space-x-8">
        {user ? (
          <form onSubmit={(e) => handleRequest(e, SignOut, router)}>
            <input type="hidden" name="pathName" value={usePathname()} />
            <button type="submit" className={s.link}>
              Sign out
            </button>
          </form>
        ) : (
          <Link href="/signin" className={s.link}>
            Sign In
          </Link>
        )}
      </div>
    </div>
  );
}

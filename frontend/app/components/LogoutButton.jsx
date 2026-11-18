
"use client";

export default function LogoutButton() {
  return (
    <form action="/auth/logout" method="POST">
      <button type="submit">
        Logout
      </button>
    </form>
  );
}
// "use client";

// import { useState } from "react";
// import { useRouter } from "next/navigation";
// import { createClient } from "@/lib/supabase/client";

// export default function LogoutButton({
//   children,
//   className,
//   style,
//   ...props
// }) {
//   const router = useRouter();
//   const [loading, setLoading] = useState(false);

//   async function handleLogout(e) {
//     e?.preventDefault?.();
//     if (loading) return;
//     setLoading(true);

//     try {
//       const supabase = createClient();
//       await supabase.auth.signOut();
//       router.push("/login");
//       router.refresh();
//     } catch (err) {
//       console.error("Sign out error:", err);
//     } finally {
//       setLoading(false);
//     }
//   }

//   return (
//     <button
//       type="button"
//       onClick={handleLogout}
//       disabled={loading}
//       className={className}
//       style={{
//         display: "inline-flex",
//         alignItems: "center",
//         justifyContent: "center",
//         gap: "8px",
//         cursor: loading ? "not-allowed" : "pointer",
//         opacity: loading ? 0.7 : 1,
//         ...style,
//       }}
//       {...props}
//     >
//       {loading ? "Signing out..." : children || "Log out"}
//     </button>
//   );
// }

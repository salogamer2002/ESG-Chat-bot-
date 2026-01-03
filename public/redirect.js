// public/redirect.js
(() => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const skip = () =>
      location.pathname.startsWith("/auth/") || location.pathname.startsWith("/login") || location.pathname.startsWith("/profile");
  
    async function run() {
      if (skip()) return;
  
      // Try for ~3s while Chainlit finishes login & sets the cookie
      for (let i = 0; i < 20; i++) {
        try {
          const res = await fetch("/api/profile-status", {
            credentials: "include", // send cookies
          });
          if (res.status === 200) {
            const { exists, email, name } = await res.json();
            if (!exists) {
              const p = new URLSearchParams({
                email: email || "",
                name: name || "",
              });
              location.replace(`/profile?${p.toString()}`);
            }
            return; // done
          }
          // 401/500 → not ready yet, retry
        } catch {
          // ignore and retry
        }
        await sleep(150);
      }
    }
  
    window.addEventListener("load", run);
  })();
  
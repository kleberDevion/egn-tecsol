import { IconBolt } from "@/components/icons";
import { ProfileMenu } from "./ProfileMenu";

export function TopBar() {
  return (
    <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-border bg-white px-4 md:px-6">
      <div className="flex items-center gap-2.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-google-blue text-white">
          <IconBolt width={18} height={18} />
        </span>
        <span className="text-lg text-ink">
          <span className="font-medium">Tecsol</span> CRM
        </span>
      </div>
      <ProfileMenu />
    </header>
  );
}

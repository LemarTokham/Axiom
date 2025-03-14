import {useState} from "react";
import {Link, NavLink} from "react-router";
import {Menu, X, ChevronDown} from "lucide-react";
import { DropdownMenuContent, DropdownMenuTrigger, DropdownMenu, DropdownMenuItem} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import {Avatar, AvatarFallback} from "@/components/ui/avatar";


const navbarOptions = [
    {
        route: "",
        label: "Home"
    },
    {
        route: "reports",
        label: "Reports"
    },
    {
        route: "settings",
        label: "Settings"
    }
]

export default function DashboardNavbar() {
    const [isOpen, setIsOpen] = useState(false);

    const route = location.pathname.split("/")[1];

    return (
        <nav className="bg-white border-b sticky top-0 left-0 w-full z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16 items-center">
                    <Link to="" className="text-xl font-bold text-gray-900">
                        Axiom
                    </Link>
                    <div className="hidden md:flex space-x-6">
                        {
                            navbarOptions.map((option, index) => (
                                <NavLink to={option.route} key={index}
                                         className={option.route == route ? "text-blue-600 font-semibold" : "text-sm text-gray-400 hover:text-zinc-700"}>
                                    {option.label}
                                </NavLink>
                            ))
                        }
                    </div>

                    <div className="hidden md:flex items-center space-x-4">
                        <DropdownMenu>
                            <DropdownMenuTrigger className="rounded-full" asChild>
                                <Button variant="ghost" className="flex items-center space-x-2">
                                    <Avatar className="w-8 h-8">
                                        <AvatarFallback>JD</AvatarFallback>
                                    </Avatar>
                                    <span>John Doe</span>
                                    <ChevronDown/>
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                <DropdownMenuItem asChild>
                                    <Link to="/profile">Profile</Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem asChild>
                                    <Link to="/settings">Settings</Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem asChild>
                                    <Link to="/logout">Logout</Link>
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>

                    <Button className="md:hidden" onClick={() => setIsOpen(!isOpen)}>
                        {isOpen ? <X className="w-6 h-6"/> : <Menu className="w-6 h-6"/>}
                    </Button>
                </div>
            </div>

            {isOpen && (
                <div className="md:hidden bg-white border-t border-gray-200">
                    <div className="px-4 py-2 space-y-2">
                        <NavLink to="" className="block text-gray-700 hover:text-blue-500">
                            Home
                        </NavLink>
                        <NavLink to="reports" className="block text-gray-700 hover:text-blue-500">
                            Reports
                        </NavLink>
                        <NavLink to="settings" className="block text-gray-700 hover:text-blue-500">
                            Settings
                        </NavLink>
                        <div className="border-t pt-2">
                            <NavLink to="/profile" className="block text-gray-700 hover:text-blue-500">
                                Profile
                            </NavLink>
                            <NavLink to="logout" className="block text-gray-700 hover:text-red-500">
                                Logout
                            </NavLink>
                        </div>
                    </div>
                </div>
            )}
        </nav>
    );
}
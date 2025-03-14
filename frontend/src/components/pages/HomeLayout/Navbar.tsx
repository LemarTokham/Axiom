import { Button } from "@/components/ui/button";
import {Link} from "react-router";

function Navbar() {
    return (
        <header className="border-b ">
            <div className=" h-16 inner-container flex items-center justify-between">
                <Link to="">
                    AXIOM
                </Link>
                <nav className="flex items-center justify-between gap-2">
                    <Link to="auth/log-in">
                        <Button variant="ghost">
                            Log In
                        </Button>
                    </Link>
                    <Link to="auth/sign-up">
                        <Button variant="secondary">
                            Sign Up
                        </Button>
                    </Link>
                </nav>
            </div>

        </header>
    );
}

export default Navbar;
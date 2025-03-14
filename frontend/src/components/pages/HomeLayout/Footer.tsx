import {Link} from "react-router";

function Footer() {
    return (
        <footer className="flex  h-16 justify-between inner-container items-center ">
            <div>
                <Link to="contact">
                    <button className="px-2 py-0.5 text-zinc-600 text-xs hover:underline hover:text-zinc-800 transition-all duration-150">
                        Contact
                    </button>
                </Link>
                <Link to="features">
                    <button className="px-2 py-0.5 text-zinc-600 text-xs hover:underline hover:text-zinc-800 transition-all duration-150">
                        Features
                    </button>
                </Link>
                <Link to="about-us">
                    <button className="px-2 py-0.5 text-zinc-600 text-xs hover:underline hover:text-zinc-800 transition-all duration-150">
                        About Us
                    </button>
                </Link>
            </div>
            <div className="text-zinc-600 text-xs">
                All rights reserved
            </div>
        </footer>
    );
}

export default Footer;
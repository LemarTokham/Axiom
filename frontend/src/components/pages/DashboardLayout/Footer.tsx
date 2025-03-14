import { Link } from "react-router";
import { Facebook, Twitter, Linkedin } from "lucide-react";

export default function DashboardFooter() {
    return (
        <footer className="bg-white border-t shadow-sm py-6 mt-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">

                    <div className="text-gray-600 text-sm">
                        © {new Date().getFullYear()} Axiom. All rights reserved.
                    </div>

                    <div className="flex space-x-6 text-sm hidden">
                        <Link to="/about" className="text-gray-600 hover:text-blue-500">
                            About
                        </Link>
                        <Link to="/privacy" className="text-gray-600 hover:text-blue-500">
                            Privacy Policy
                        </Link>
                        <Link to="/terms" className="text-gray-600 hover:text-blue-500">
                            Terms of Service
                        </Link>
                    </div>

                    {/* Right: Social Media Icons */}
                    <div className="flex space-x-4">
                        <a href="https://facebook.com" target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-blue-600">
                            <Facebook className="w-5 h-5" />
                        </a>
                        <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-blue-500">
                            <Twitter className="w-5 h-5" />
                        </a>
                        <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-blue-700">
                            <Linkedin className="w-5 h-5" />
                        </a>
                    </div>
                </div>
            </div>
        </footer>
    );
}

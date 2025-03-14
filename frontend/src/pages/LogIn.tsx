import {Eye, EyeOff} from "lucide-react";
import {
    useState
} from "react"
import {
    toast
} from "sonner"
import {
    useForm
} from "react-hook-form"
import {
    zodResolver
} from "@hookform/resolvers/zod"
import * as z from "zod"

import {
    Button
} from "@/components/ui/button"
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form"
import {
    Input
} from "@/components/ui/input"


function LogIn() {
    return (
        <div className="flex-1 flex items-center justify-center">
            <div className="flex flex-col items-center justify-center w-full">
                <h1 className="font-semibold text-xl">
                    Welcome Back
                </h1>
                <MyForm/>
            </div>
        </div>
    );
}


const formSchema = z.object({
    email: z.string(),
    password: z.string().min(1).min(6).max(12)
});

function MyForm() {

    const [showPassword, setShowPassword] = useState<boolean>(false);

    const form = useForm < z.infer < typeof formSchema >> ({
        resolver: zodResolver(formSchema),

    })

    function onSubmit(values: z.infer < typeof formSchema > ) {
        try {
            console.log(values);
            toast(
                <pre className="mt-2 w-[340px] rounded-md bg-slate-950 p-4">
          <code className="text-white">{JSON.stringify(values, null, 2)}</code>
        </pre>
            );
        } catch (error) {
            console.error("Form submission error", error);
            toast.error("Failed to submit the form. Please try again.");
        }
    }

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 py-10 w-full max-w-[500px]">

                <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Email</FormLabel>
                            <FormControl className="">
                                <Input
                                    placeholder="johndoe@mail.com"

                                    type="email"
                                    {...field} />
                            </FormControl>
                            <FormDescription>Enter your email</FormDescription>
                            <FormMessage />
                        </FormItem>
                    )}
                />

                <FormField
                    control={form.control}
                    name="password"
                    render={({ field }) => (
                        <FormItem>
                            <FormLabel>Password</FormLabel>
                            <FormControl>
                                <div className="relative">
                                    <Input
                                        placeholder="******"
                                        type={showPassword ? "text" : "password"}
                                        {...field}
                                    />
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="icon"
                                        className="absolute right-2 top-1/2 w-fit h-fit pr-2 transform -translate-y-1/2 hover:bg-white cursor-pointer"
                                        onClick={() => setShowPassword((prev) => !prev)}
                                    >
                                        {showPassword ? <EyeOff size={18}/> : <Eye size={18}/>}
                                    </Button>
                                </div>
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />

                <Button type="submit">Submit</Button>
            </form>
        </Form>
    )
}


export default LogIn;
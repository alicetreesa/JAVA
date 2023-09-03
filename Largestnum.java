import java.util.Scanner;
class largest
{
 public static void main(String args[])
{
 Scanner reader = new Scanner(System.in);
 System.out.print("Enter first number:");
 int a = reader.nextInt();
 System.out.print("Enter second number:");
 int b = reader.nextInt();
 System.out.print("Enter third number:");
 int c = reader.nextInt();

if(a>=b && a>=c)
System.out.println(a+ " is the largest number");
else if(b>=a && b>=c)
System.out.println(b+ " is the largest number");
else
System.out.println(c+ " is the largest number");
}
}

 
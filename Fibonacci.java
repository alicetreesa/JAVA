import java.util.Scanner;
class Fibonacci
{
 public static void main(String args[])
{
int a=0,b=1,c,i;
Scanner reader = new Scanner(System.in);
System.out.print("Enter the number of elements:");
int num = reader.nextInt();
System.out.print(a+" "+b);
for(i=2;i<num;++i)
{ 
 c=a+b;
 System.out.print(" "+c);
 a=b;
 b=c;
}
}
}
 